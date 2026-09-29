.PHONY: build test

test:
	go test ./...

build:
	mkdir -p dist
	GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -o dist/windows-amd64.exe .
	GOOS=windows GOARCH=arm64 CGO_ENABLED=0 go build -o dist/windows-arm64.exe .
	GOOS=darwin GOARCH=amd64 CGO_ENABLED=0 go build -o dist/macos-amd64 .
	GOOS=darwin GOARCH=arm64 CGO_ENABLED=0 go build -o dist/macos-arm64 .
	GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -o dist/linux-amd64 .
	GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o dist/linux-arm64 .
