package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"time"
)

type identity struct {
	Platform    string            `json:"platform"`
	DeviceID    string            `json:"device_id"`
	Identifiers map[string]string `json:"identifiers"`
	Hostname    string            `json:"hostname"`
}

type scanConfig struct {
	ServerURL    string            `json:"server_url"`
	SessionID    string            `json:"session_id"`
	ScanToken    string            `json:"scan_token"`
	BinarySHA256 map[string]string `json:"binary_sha256"`
}

func verifyExecutableChecksum(path string, expected map[string]string) error {
	want := expected[filepath.Base(path)]
	if want == "" {
		return nil
	}
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	hash := sha256.New()
	if _, err := io.Copy(hash, file); err != nil {
		file.Close()
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	if actual := hex.EncodeToString(hash.Sum(nil)); !strings.EqualFold(actual, want) {
		return errors.New("helper checksum verification failed")
	}
	return nil
}

func parseRegistryValue(output, name string) string {
	pattern := regexp.MustCompile(`(?im)^\s*` + regexp.QuoteMeta(name) + `\s+REG_\w+\s+(.+?)\s*$`)
	match := pattern.FindStringSubmatch(output)
	if len(match) < 2 {
		return ""
	}
	return strings.TrimSpace(match[1])
}

func parseIORegValue(output, name string) string {
	pattern := regexp.MustCompile(`"` + regexp.QuoteMeta(name) + `"\s*=\s*"([^"]+)"`)
	match := pattern.FindStringSubmatch(output)
	if len(match) < 2 {
		return ""
	}
	return strings.TrimSpace(match[1])
}

func lookupNative(key string) (string, error) {
	switch key {
	case "windows.machine_guid", "windows.product_id":
		path, name := `HKLM\SOFTWARE\Microsoft\Cryptography`, "MachineGuid"
		if key == "windows.product_id" {
			path, name = `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion`, "ProductId"
		}
		output, err := exec.Command("reg", "query", path, "/v", name).Output()
		if err != nil {
			return "", err
		}
		return parseRegistryValue(string(output), name), nil
	case "macos.platform_uuid", "macos.serial":
		output, err := exec.Command("ioreg", "-rd1", "-c", "IOPlatformExpertDevice").Output()
		if err != nil {
			return "", err
		}
		name := "IOPlatformUUID"
		if key == "macos.serial" {
			name = "IOPlatformSerialNumber"
		}
		return parseIORegValue(string(output), name), nil
	case "linux.machine_id", "linux.product_uuid":
		path := "/etc/machine-id"
		if key == "linux.product_uuid" {
			path = "/sys/class/dmi/id/product_uuid"
		}
		value, err := os.ReadFile(path)
		if err != nil {
			return "", err
		}
		return strings.TrimSpace(string(value)), nil
	default:
		return "", errors.New("unsupported identifier")
	}
}

func collectIdentity(platform string, lookup func(string) (string, error)) (identity, error) {
	keys := map[string][]string{
		"windows": {"machine_guid", "product_id"},
		"macos":   {"platform_uuid", "serial"},
		"linux":   {"machine_id", "product_uuid"},
	}[platform]
	if len(keys) == 0 {
		return identity{}, errors.New("unsupported operating system")
	}
	primary, err := lookup(platform + "." + keys[0])
	if err != nil || strings.TrimSpace(primary) == "" {
		return identity{}, fmt.Errorf("required %s unavailable", keys[0])
	}
	identifiers := map[string]string{keys[0]: strings.TrimSpace(primary)}
	if second, err := lookup(platform + "." + keys[1]); err == nil && strings.TrimSpace(second) != "" {
		identifiers[keys[1]] = strings.TrimSpace(second)
	}
	hostname, _ := os.Hostname()
	return identity{
		Platform: platform, DeviceID: identifiers[keys[0]],
		Identifiers: identifiers, Hostname: hostname,
	}, nil
}

func platformName() string {
	if runtime.GOOS == "darwin" {
		return "macos"
	}
	return runtime.GOOS
}

func run() error {
	executable, err := os.Executable()
	if err != nil {
		return err
	}
	configBytes, err := os.ReadFile(filepath.Join(filepath.Dir(executable), "scan.json"))
	if err != nil {
		return fmt.Errorf("scan.json unavailable: %w", err)
	}
	var config scanConfig
	if err := json.Unmarshal(configBytes, &config); err != nil {
		return fmt.Errorf("invalid scan.json: %w", err)
	}
	if config.ServerURL == "" || config.SessionID == "" || config.ScanToken == "" {
		return errors.New("incomplete scan.json")
	}
	if err := verifyExecutableChecksum(executable, config.BinarySHA256); err != nil {
		return err
	}
	if !strings.HasPrefix(config.ServerURL, "https://") &&
		!strings.HasPrefix(config.ServerURL, "http://localhost:") &&
		!strings.HasPrefix(config.ServerURL, "http://127.0.0.1:") {
		return errors.New("registration server must use HTTPS")
	}
	found, err := collectIdentity(platformName(), lookupNative)
	if err != nil {
		return err
	}
	fmt.Println("BioGuard registration: device identity collected")
	payload := map[string]interface{}{
		"scan_token": config.ScanToken, "platform": found.Platform,
		"device_id": found.DeviceID, "identifiers": found.Identifiers,
		"hostname": found.Hostname,
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	endpoint := strings.TrimRight(config.ServerURL, "/") +
		"/api/devices/browser-enrollment/session/" + config.SessionID + "/identity/"
	request, err := http.NewRequest(http.MethodPost, endpoint, bytes.NewReader(body))
	if err != nil {
		return err
	}
	request.Header.Set("Content-Type", "application/json")
	client := &http.Client{
		Timeout:   15 * time.Second,
		Transport: &http.Transport{ForceAttemptHTTP2: false},
	}
	fmt.Println("BioGuard registration: sending identity")
	response, err := client.Do(request)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	result, err := io.ReadAll(io.LimitReader(response.Body, 4096))
	if err != nil {
		return err
	}
	if response.StatusCode != http.StatusOK {
		var failure struct {
			Error string `json:"error"`
		}
		_ = json.Unmarshal(result, &failure)
		return fmt.Errorf("registration failed (%d): %s", response.StatusCode, failure.Error)
	}
	fmt.Println("PC ma'lumotlari yuborildi. Browser'dagi QR kodni admin skaner qilib tasdiqlasin.")
	return nil
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "BioGuard registration:", err)
		os.Exit(1)
	}
}
