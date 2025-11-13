import socket
import requests
import whois
import tldextract

class UrlsChecker:
    result = {
        "input_url": "",
        "domain": None,
        "ip": None,
        "country": None,
        "asn": None,
        "org": None,
        "registrar": None,
        "creation_date": None,
        "expiration_date": None,
        "name_servers": [],
        "russian_traces": [],
        "errors": []
    }
    def __init__(self, urls: list[str] | str):
        self.urls = [urls] if isinstance(urls, str) else urls
    def normalize_url(self, url: str) -> str:
        try:
            ext = tldextract.extract(url)
            domain = f"{ext.domain}.{ext.suffix}"
            self.result["domain"] = domain
        except Exception as e:
            self.result["errors"].append(f"Domain parse error: {e}")
            return self.result
    def whois_lookup(self):
        try:
            w = whois.whois(self.result["domain"])
            self.result["registrar"] = w.registrar
            self.result["creation_date"] = str(w.creation_date)
            self.result["expiration_date"] = str(w.expiration_date)
            if isinstance(w.name_servers, list):
                self.result["name_servers"] = [ns.lower() for ns in w.name_servers]
            elif w.name_servers:
                self.result["name_servers"] = [str(w.name_servers).lower()]
        except Exception as e:
            self.result["errors"].append(f"WHOIS error: {e}")
    def get_ip_info(self):
        try:
            ip = socket.gethostbyname(self.result["domain"])
            geo = requests.get(f"https://ipapi.co/{ip}/json/", timeout=8).json()
            self.result["ip"] = ip
            self.result["country"] = geo.get("country_name")
            self.result["asn"] = geo.get("asn")
            self.result["org"] = geo.get("org")
        except Exception as e:
            self.result["errors"].append(f"Geo lookup error: {e}")
    def validate_russian_traces(self):
        ru_traces = []
        ru_keywords = [
            "ru-center", "reg.ru", "beget", "timeweb", "masterhost", "yandex",
            "rambler", "rostelecom", ".ru", ".su", ".rf", "hostland"
        ]

        # TLD check
        if self.result["domain"].endswith((".ru", ".su", ".rf")):
            ru_traces.append("TLD російський (.ru/.su/.rf)")

        # Registrar check
        reg = (self.result["registrar"] or "").lower()
        if any(k in reg for k in ru_keywords):
            ru_traces.append("Російський реєстратор")

        # IP country
        if self.result["country"] == "Russia":
            ru_traces.append("Хостинг розташований у РФ")

        # DNS servers
        if any(".ru" in ns for ns in self.result["name_servers"]):
            ru_traces.append("DNS сервер у РФ")

        self.result["russian_traces"] = ru_traces or ["Ознак РФ не виявлено"]
    def get_domain_metadata(self, url: str) -> dict:
        self.result["input_url"] = url
        self.normalize_url(url)
        if not self.result["domain"]:
            return self.result
        self.whois_lookup()
        self.get_ip_info()
        self.validate_russian_traces()
        return self.result
    def run(self) -> list[dict]:
        if not self.urls:
            return []
        if isinstance(self.urls, str):
            self.urls = [self.urls]
        return [self.get_domain_metadata(url) for url in self.urls]