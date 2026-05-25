-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    cpf VARCHAR(11) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    telefone VARCHAR(20)
);

-- Tabela de Veículos
CREATE TABLE IF NOT EXISTS veiculos (
    id_veiculo SERIAL PRIMARY KEY,
    placa VARCHAR(7) UNIQUE,
    modelo VARCHAR(50) NOT NULL,
    ano INTEGER
);

-- Tabela de Setores
CREATE TABLE IF NOT EXISTS setores (
    id_setor SERIAL PRIMARY KEY,
    nome_setor VARCHAR(50) NOT NULL
);

-- Tabela de Reservas (Tickets)
CREATE TABLE IF NOT EXISTS reservas (
    id_reserva SERIAL PRIMARY KEY,
    id_usuario INTEGER REFERENCES usuarios(id_usuario),
    id_veiculo INTEGER REFERENCES veiculos(id_veiculo),
    id_setor INTEGER REFERENCES setores(id_setor),
    hora_inicio TIMESTAMP NOT NULL,
    hora_fim TIMESTAMP NOT NULL
);