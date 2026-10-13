"""BioGuard entrypoint; platform integration loads only when started."""

def main():
    import sys
    if sys.argv[1:] == ['--installer-activation']:
        from app.installer_activation import run
        run()
        return
    from app.bootstrap import run
    run()


if __name__ == "__main__":
    main()
