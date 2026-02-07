from django.core.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    default_port = "5000"

    def handle(self, *args, **options):
        self._print_links(options)
        return super().handle(*args, **options)

    def _print_links(self, options):
        addrport = options.get("addrport") or ""
        default_port = str(getattr(self, "default_port", "8000"))
        if addrport:
            if ":" in addrport:
                host, port = addrport.rsplit(":", 1)
            else:
                host, port = addrport, default_port
        else:
            host, port = "127.0.0.1", default_port

        if host in ("", "0", "0.0.0.0", "::"):
            host = "127.0.0.1"

        base = f"http://{host}:{port}"
        self.stdout.write(self.style.SUCCESS(f"Home:  {base}/"))
        self.stdout.write(self.style.SUCCESS(f"Login: {base}/accounts/login/"))
