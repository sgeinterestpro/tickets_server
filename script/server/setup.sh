# Install Mongodb for Debian 10
wget https://repo.mongodb.org/apt/debian/dists/buster/mongodb-org/4.4/main/binary-amd64/mongodb-org-server_4.4.1_amd64.deb
apt install mongodb-org-server_4.4.1_amd64.deb

# Install Python build dependencies 
apt update; apt install -y --no-install-recommends make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install Pyenv
apt install -y git python3-pip
curl https://pyenv.run | bash
cat << EOF >> ~/.bashrc

# 3 line for pyenv
export PATH="/root/.pyenv/bin:$PATH"
eval "\$(pyenv init -)"
eval "\$(pyenv virtualenv-init -)"

EOF
source .bashrc

# Create tickets virtualenv
pyenv virtualenv 3.7.2 tickets_server

# Clone tickets_server
git clone https://hub.fastgit.org/sgeinterestpro/tickets_server.git

# Set virtualenv auto activate
cd tickets_server
pyenv activate tickets_server
pyenv local tickets_server

# Install requirements
pip install -r requirements.txt