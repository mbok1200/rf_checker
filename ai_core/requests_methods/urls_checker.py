import socket
import requests
import whois
import tldextract
import dns.resolver  # pip install dnspython

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
        "nameserver_countries": [],  # NEW
        "hosting_provider": None,  # NEW
        "dns_records": {},  # NEW
        "ssl_issuer": None,  # NEW
        "russian_traces": [],
        "errors": [],
        "whois_server": None,  # NEW: WHOIS сервер (вказує на країну реєстрації)
        "registrant_country": None,  # NEW: Країна власника з WHOIS
        "admin_country": None,  # NEW: Країна адміністратора
        "tech_country": None,  # NEW: Країна технічного контакту
        "registry_domain_id": None,  # NEW: ID реєстру
        "dnssec": None,  # NEW: DNSSEC статус
        "abuse_contact": None,  # NEW: Контакт для скарг
        "status": [],  # NEW: Статуси домену
        "rdap_info": {},  # NEW: RDAP дані (новіший протокол замість WHOIS)
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
            
            # NEW: Додаткові WHOIS поля
            self.result["whois_server"] = getattr(w, 'whois_server', None)
            self.result["registrant_country"] = getattr(w, 'registrant_country', None) or getattr(w, 'country', None)
            self.result["admin_country"] = getattr(w, 'admin_country', None)
            self.result["tech_country"] = getattr(w, 'tech_country', None)
            self.result["dnssec"] = getattr(w, 'dnssec', None)
            self.result["status"] = getattr(w, 'status', [])
            
            if isinstance(w.name_servers, list):
                self.result["name_servers"] = [ns.lower() for ns in w.name_servers]
            elif w.name_servers:
                self.result["name_servers"] = [str(w.name_servers).lower()]
        except Exception as e:
            self.result["errors"].append(f"WHOIS error: {e}")
    def get_ip_info(self):
        try:
            try:
                ip = socket.gethostbyname(self.result["domain"])
                self.result["ip"] = ip
            except socket.gaierror as e:
                self.result["errors"].append(f"IP resolution error: {e}")
                return  # Exit early if can't resolve IP
        
            # Only try geo lookup if we have valid IP
            if ip:
                geo = requests.get(f"https://ipapi.co/{ip}/json/", timeout=8).json()
                self.result["country"] = geo.get("country_name")
                self.result["asn"] = geo.get("asn")
                self.result["org"] = geo.get("org")
        except Exception as e:
            self.result["errors"].append(f"Geo lookup error: {e}")
    def check_nameserver_location(self):
        """Визначає країни DNS серверів"""
        try:
            ns_countries = []
            for ns in self.result["name_servers"]:
                try:
                    ns_ip = socket.gethostbyname(ns)
                    geo = requests.get(f"https://ipapi.co/{ns_ip}/json/", timeout=5).json()
                    country = geo.get("country_name", "Unknown")
                    ns_countries.append(f"{ns}: {country}")
                except:
                    pass
            self.result["nameserver_countries"] = ns_countries
        except Exception as e:
            self.result["errors"].append(f"NS location error: {e}")
    def check_dns_records(self):
        """Перевіряє MX, TXT записи для виявлення провайдера"""
        try:
            resolver = dns.resolver.Resolver()
            
            # MX records (email servers)
            try:
                mx_records = resolver.resolve(self.result["domain"], 'MX')
                self.result["dns_records"]["mx"] = [str(r.exchange) for r in mx_records]
            except:
                pass
            
            # TXT records (може містити інфо про провайдера)
            try:
                txt_records = resolver.resolve(self.result["domain"], 'TXT')
                self.result["dns_records"]["txt"] = [str(r) for r in txt_records]
            except:
                pass
                
        except Exception as e:
            self.result["errors"].append(f"DNS records error: {e}")
    def check_ssl_certificate(self):
        """Перевіряє SSL сертифікат"""
        try:
            import ssl
            import OpenSSL  # pip install pyopenssl
            
            cert = ssl.get_server_certificate((self.result["domain"], 443))
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
            issuer = dict(x509.get_issuer().get_components())
            
            self.result["ssl_issuer"] = issuer.get(b'O', b'').decode('utf-8')
        except Exception as e:
            self.result["errors"].append(f"SSL check error: {e}")
    def detect_hosting_provider(self):
        """Визначає хостинг-провайдера"""
        org = (self.result.get("org") or "").lower()
        
        hosting_map = {
            "cloudflare": "Cloudflare",
            "amazon": "AWS",
            "google": "Google Cloud",
            "microsoft": "Azure",
            "digitalocean": "DigitalOcean",
            "ovh": "OVH",
            "hetzner": "Hetzner",
            "selectel": "Selectel (RU)",
            "beget": "Beget (RU)",
            "reg.ru": "Reg.ru (RU)",
            "timeweb": "Timeweb (RU)"
        }
        
        for key, provider in hosting_map.items():
            if key in org:
                self.result["hosting_provider"] = provider
                break
    def check_rdap(self):
        """RDAP - новіший протокол для інформації про домени"""
        try:
            from ipwhois import IPWhois
            
            if self.result["ip"]:
                obj = IPWhois(self.result["ip"])
                rdap = obj.lookup_rdap()
                
                self.result["rdap_info"] = {
                    "asn_country_code": rdap.get("asn_country_code"),
                    "asn_description": rdap.get("asn_description"),
                    "network_name": rdap.get("network", {}).get("name"),
                    "network_country": rdap.get("network", {}).get("country"),
                }
        except Exception as e:
            self.result["errors"].append(f"RDAP error: {e}")
    def check_ccTLD_registrar(self):
        """Перевіряє реєстратора для ccTLD (національних доменів)"""
        tld = self.result["domain"].split('.')[-1]
        
        # Мапа національних доменів і їх WHOIS серверів
        cctld_map = {
            "ru": "whois.tcinet.ru",
            "su": "whois.tcinet.ru", 
            "рф": "whois.tcinet.ru",
            "by": "whois.cctld.by",
            "ua": "whois.ua",
            "kz": "whois.nic.kz",
        }
        
        if tld in cctld_map:
            self.result["whois_server"] = cctld_map[tld]
            return True
        return False
    def check_rir_allocation(self):
        """Перевіряє Regional Internet Registry (хто виділив IP блок)"""
        rir_map = {
            "RIPE NCC": ["Europe", "Middle East", "Russia"],
            "ARIN": ["North America"],
            "APNIC": ["Asia Pacific"],
            "LACNIC": ["Latin America"],
            "AFRINIC": ["Africa"]
        }
        
        org = (self.result.get("org") or "").lower()
        for rir, regions in rir_map.items():
            if rir.lower() in org:
                self.result["rir"] = rir
                break
    def validate_russian_traces(self):
        ru_traces = []
        ru_keywords = [
            "ru-center", "reg.ru", "beget", "timeweb", "masterhost", "yandex",
            "rambler", "rostelecom", ".ru", ".su", ".rf", "hostland", "selectel"
        ]

        # TLD check
        if self.result["domain"].endswith((".ru", ".su", ".rf")):
            ru_traces.append("TLD російський (.ru/.su/.rf)")

        # Registrar check
        reg = (self.result["registrar"] or "").lower()
        if any(k in reg for k in ru_keywords):
            ru_traces.append(f"Російський реєстратор: {self.result['registrar']}")

        # IP country
        if self.result["country"] == "Russia":
            ru_traces.append("Хостинг розташований у РФ")

        # DNS servers
        if any(".ru" in ns for ns in self.result["name_servers"]):
            ru_traces.append("DNS сервер у РФ")
        
        # NEW: Nameserver countries
        if any("Russia" in ns for ns in self.result.get("nameserver_countries", [])):
            ru_traces.append("DNS сервер фізично у РФ")
        
        # NEW: Hosting provider
        if self.result.get("hosting_provider") and "(RU)" in self.result["hosting_provider"]:
            ru_traces.append(f"Російський хостинг: {self.result['hosting_provider']}")
        
        # NEW: MX records
        mx_records = self.result.get("dns_records", {}).get("mx", [])
        if any(".ru" in mx for mx in mx_records):
            ru_traces.append("Email сервер у РФ")

        # NEW: WHOIS сервер
        if self.result.get("whois_server") and ".ru" in str(self.result["whois_server"]):
            ru_traces.append("WHOIS сервер російський")
        
        # NEW: Країна реєстранта
        countries = [
            self.result.get("registrant_country"),
            self.result.get("admin_country"), 
            self.result.get("tech_country")
        ]
        if any(c and "RU" in str(c).upper() for c in countries):
            ru_traces.append("Контактна особа з РФ")
        
        # NEW: RDAP дані
        rdap = self.result.get("rdap_info", {})
        if rdap.get("asn_country_code") == "RU":
            ru_traces.append("ASN зареєстрований у РФ")
    
        self.result["russian_traces"] = ru_traces or ["Ознак РФ не виявлено"]
    def check_http_headers(self):
        """Перевіряє HTTP заголовки для визначення сервера"""
        try:
            response = requests.get(f"https://{self.result['domain']}", timeout=5)
            headers = response.headers
            
            self.result["http_headers"] = {
                "server": headers.get("Server"),
                "x-powered-by": headers.get("X-Powered-By"),
                "cf-ray": headers.get("CF-RAY"),  # Cloudflare
            }
            
            # Detect Russian hosting by headers
            server = str(headers.get("Server", "")).lower()
            if any(x in server for x in ["nginx/", "apache/", "yandex"]):
                if self.result["country"] == "Russia":
                    self.result["russian_traces"].append(f"HTTP Server у РФ: {server}")
                    
        except Exception as e:
            self.result["errors"].append(f"HTTP headers error: {e}")
    def check_autonomous_system(self):
        """Детальна перевірка ASN"""
        if self.result.get("asn"):
            # Common Russian ASNs
            russian_asns = {
                "AS8359": "MTS",
                "AS12389": "Rostelecom",
                "AS47764": "VKontakte",
                "AS13238": "Yandex",
                "AS31213": "Megafon",
            }
            
            asn = str(self.result["asn"])
            if asn in russian_asns:
                self.result["russian_traces"].append(f"Російський ASN: {russian_asns[asn]}")
    def get_domain_metadata(self, url: str) -> dict:
        # Reset result for each URL
        self.result = {
            "input_url": url,
            "domain": None,
            "ip": None,
            "country": None,
            "asn": None,
            "org": None,
            "registrar": None,
            "creation_date": None,
            "expiration_date": None,
            "name_servers": [],
            "nameserver_countries": [],
            "hosting_provider": None,
            "dns_records": {},
            "ssl_issuer": None,
            "russian_traces": [],
            "errors": [],
            "whois_server": None,
            "registrant_country": None,
            "admin_country": None,
            "tech_country": None,
            "registry_domain_id": None,
            "dnssec": None,
            "abuse_contact": None,
            "status": [],
            "rdap_info": {},
        }
        
        self.normalize_url(url)
        if not self.result["domain"]:
            return self.result
        
        self.whois_lookup()
        self.get_ip_info()
        self.check_rdap()
        self.check_ccTLD_registrar()
        self.check_rir_allocation()
        self.detect_hosting_provider()
        self.check_nameserver_location()
        self.check_dns_records()
        self.check_ssl_certificate()
        self.check_http_headers()  # NEW
        self.check_autonomous_system()  # NEW
        self.validate_russian_traces()
        
        return self.result
    def run(self) -> list[dict]:
        if not self.urls:
            return []
        if isinstance(self.urls, str):
            self.urls = [self.urls]
        return [self.get_domain_metadata(url) for url in self.urls]