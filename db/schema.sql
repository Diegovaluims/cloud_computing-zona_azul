-- Recriando tabelas para zerar o estado
DROP TABLE IF EXISTS usuario_veiculo, reservas, setores, veiculos, usuarios CASCADE;

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL
);

-- Tabela de Veículos
CREATE TABLE IF NOT EXISTS veiculos (
    id_veiculo SERIAL PRIMARY KEY,
    placa VARCHAR(50) UNIQUE,
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
    id_setor INTEGER REFERENCES setores(id_setor)
);

-- Tabela ponte entre o usuário e seus veículos salvos
CREATE TABLE IF NOT EXISTS usuario_veiculo (
    id_usuario INTEGER REFERENCES usuarios(id_usuario),
    placa VARCHAR(50) REFERENCES veiculos(placa),
    PRIMARY KEY (id_usuario, placa)
);