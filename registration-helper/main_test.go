package main

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func TestExecutableChecksum(t *testing.T) {
	file, err := os.CreateTemp(t.TempDir(), "helper")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := file.WriteString("signed-helper"); err != nil {
		t.Fatal(err)
	}
	if err := file.Close(); err != nil {
		t.Fatal(err)
	}
	hash := sha256.Sum256([]byte("signed-helper"))
	if err := verifyExecutableChecksum(file.Name(), map[string]string{
		filepath.Base(file.Name()): hex.EncodeToString(hash[:]),
	}); err != nil {
		t.Fatal(err)
	}
	if err := verifyExecutableChecksum(file.Name(), map[string]string{
		filepath.Base(file.Name()): "bad-checksum",
	}); err == nil {
		t.Fatal("expected checksum failure")
	}
}

func TestParseRegistryValue(t *testing.T) {
	sample := "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography\r\n    MachineGuid    REG_SZ    1234-ABCD\r\n"
	if got := parseRegistryValue(sample, "MachineGuid"); got != "1234-ABCD" {
		t.Fatalf("got %q", got)
	}
}

func TestParseIORegValue(t *testing.T) {
	sample := `  |   "IOPlatformUUID" = "MAC-UUID"` + "\n"
	if got := parseIORegValue(sample, "IOPlatformUUID"); got != "MAC-UUID" {
		t.Fatalf("got %q", got)
	}
}

func TestCollectIdentityUsesPlatformIdentifiers(t *testing.T) {
	values := map[string]string{
		"linux.machine_id": "linux-id", "linux.product_uuid": "product-uuid",
		"macos.platform_uuid": "mac-uuid", "macos.serial": "serial-1",
		"windows.machine_guid": "win-guid", "windows.product_id": "win-product",
	}
	lookup := func(key string) (string, error) { return values[key], nil }
	cases := []struct{ platform, id, key string }{
		{"linux", "linux-id", "machine_id"},
		{"macos", "mac-uuid", "platform_uuid"},
		{"windows", "win-guid", "machine_guid"},
	}
	for _, tc := range cases {
		got, err := collectIdentity(tc.platform, lookup)
		if err != nil {
			t.Fatalf("%s: %v", tc.platform, err)
		}
		if got.DeviceID != tc.id || got.Identifiers[tc.key] != tc.id {
			t.Fatalf("%s: wrong identity: %+v", tc.platform, got)
		}
	}
}

func TestCollectIdentityRejectsMissingPrimary(t *testing.T) {
	lookup := func(key string) (string, error) { return "", errors.New("missing") }
	if _, err := collectIdentity("linux", lookup); err == nil {
		t.Fatal("expected missing machine-id to fail")
	}
}
