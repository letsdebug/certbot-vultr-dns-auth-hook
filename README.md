# certbot-vultr-dns-auth-hook

This is an "auth hook" for Certbot that enables you to perform DNS-01 authorization via Vultr's DNS service.

All it requires is that you have your [Vultr API key](https://my.vultr.com/settings/#settingsapi), and that you have set your domain up [as a zone in Vultr](https://my.vultr.com/dns/).

## Usage

These instructions assume you are on a shell as the `root` user.

1. Download `vultr-dns.py` somewhere onto your server. In this example, we will use `/etc/letsencrypt/vultr-dns.py` as the location.
2. `chmod 0700 /etc/letsencrypt/vultr-dns.py && chown root:root /etc/letsencrypt/vultr-dns.py`
3. Modify the configuration section of `/etc/letsencrypt/vultr-dns.py` :

```python
# Configure here
VULTR_API_KEY = "put your api key here"
VULTR_BIND_DELAY = 30
```

4. Try issue a certificate now. With the default configuration, there will be a 30 second delay per domain on the certificate.

```bash
certbot certonly --manual \
--manual-auth-hook "/etc/letsencrypt/vultr-dns.py create" \
--manual-cleanup-hook "/etc/letsencrypt/vultr-dns.py delete" \
-d "*.my.domain.example.com" -d "*.example.com" \
--preferred-challenges dns-01
```
5. If this succeeds, so should automatic renewal.