# 1. Busca dinamicamente a imagem mais recente do Ubuntu 22.04 LTS na AWS
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # ID oficial da Canonical (criadora do Ubuntu)

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# 2. Configura o Firewall da máquina (Security Group)
resource "aws_security_group" "zona_azul_sg" {
  name        = "zona_azul_sg"
  description = "Acesso para o sistema Zona Azul"

  # Libera a porta 8000 para a API do Usuário
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Libera a porta 8001 para a API do Fiscal
  ingress {
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Libera a porta 22 (Caso você queira acessar a máquina via SSH futuramente)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Libera a saída da máquina para a internet (Necessário para baixar o Docker)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Faz o upload da sua chave pública local para a AWS
resource "aws_key_pair" "acesso_ssh" {
  key_name   = "chave-zona-azul"
  public_key = file("~/.ssh/zona_azul_key.pub")
}

# 3. Criação da Instância EC2
resource "aws_instance" "backend_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro" # Elegível para o plano gratuito
  key_name      = aws_key_pair.acesso_ssh.key_name

  # Atrela o grupo de segurança criado acima à máquina
  vpc_security_group_ids = [aws_security_group.zona_azul_sg.id]

  # Script de automação (User Data): Executado uma única vez assim que a máquina liga
  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update -y
              
              # Instala o Docker
              sudo apt-get install -y docker.io
              sudo service docker start
              sudo systemctl start docker
              sudo systemctl enable docker
              
              # Instala o Docker Compose v2
              sudo mkdir -p /usr/local/lib/docker/cli-plugins/
              sudo curl -SL https://github.com/docker/compose/releases/download/v2.36.2/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
              sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
              
              # Cria uma pasta para o projeto, clona o repositório e sobe os contêineres
              mkdir -p /home/ubuntu/app
              cd /home/ubuntu/app
              
              git clone -b dev https://github.com/Diegovaluims/cloud_computing-zona_azul.git .
              
              # Executa o compose usando o plugin v2
              sudo docker compose up -d --build
              EOF

  tags = {
    Name = "ZonaAzul-Backend"
  }
}

# 4. IP Elástico (Elastic IP) — mantém o IP fixo mesmo após stop/start da instância
resource "aws_eip" "backend_ip" {
  instance = aws_instance.backend_server.id

  tags = {
    Name = "ZonaAzul-ElasticIP"
  }
}

output "ip_publico_backend" {
  description = "IP fixo (Elastic IP) do backend — use este nos arquivos JS do frontend"
  value       = aws_eip.backend_ip.public_ip
}