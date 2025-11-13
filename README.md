# vpn_wireguard_mirror_bot
Interactive telegram bot for automate VPN clients. Based on async aiogram.

## Installation
```bash
git clone https://github.com/feel2code/vpn_wireguard_mirror_bot.git
cd vpn_wireguard_mirror_bot
pip install -r requirements.txt
```
## Configuration
```bash
cp env.template .env
```
Edit `.env` file and set the following variables:
```bash
BOT_TOKEN=
SERVICE_NAME=
ADMIN=
FS_USER=
DB_NAME=
DEMO_REGIME=1
HOST_AND_PORT=
```

## Run
```bash
python3 main.py
```

## Features
- [x] Wireguard
- [x] proxy

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Planning:
- [ ] Need to update architecture to use flags in db for each service (wg, proxy, vray)
