# bug-free-dollop
Send me a random CFA ethics example every day

Initialize after cloning with:

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Systemd service `/etc/systemd/system/bug-free-dollop.service`
```ini
[Unit]
Description=Ethics Buddy Telegram Bot
After=network.target

[Service]
Type=simple
User=bxa
WorkingDirectory=/home/bxa/bug-free-dollop
ExecStart=/usr/bin/python3 /home/bxa/bug-free-dollop/ethicsbuddy.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

To activate:
```shell
sudo systemctl daemon-reload
sudo systemctl enable --now bug-free-dollop
sudo systemctl start --now bug-free-dollop
```