-- ============================================================
-- Schema do Banco de Dados - Zona Azul
-- Este arquivo é executado automaticamente pelo PostgreSQL
-- na inicialização do contêner via docker-entrypoint-initdb.d/
-- ============================================================

-- Reset de estado: garante ambiente limpo a cada rebuild com 'docker-compose down -v'
DROP TABLE IF EXISTS usuario_veiculo, reservas, veiculos, usuarios CASCADE;

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY, -- SERIAL: autoincremento gerenciado pelo PostgreSQL
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE
);

-- Tabela de Veículos
CREATE TABLE IF NOT EXISTS veiculos (
    id_veiculo SERIAL PRIMARY KEY,
    placa VARCHAR(50) UNIQUE,       -- UNIQUE: uma placa só pode existir uma vez no sistema
    modelo VARCHAR(50) NOT NULL,
    ano INTEGER
);

-- Tabela de Reservas (Tickets)
CREATE TABLE IF NOT EXISTS reservas (
    id_reserva SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE, -- FK: integridade referencial com usuarios
    id_veiculo INTEGER NOT NULL REFERENCES veiculos(id_veiculo) ON DELETE CASCADE  -- FK: integridade referencial com veiculos
);

-- Tabela ponte entre usuário e seus veículos (relação N:N)
-- PRIMARY KEY composta: impede que o mesmo usuário vincule a mesma placa duas vezes
CREATE TABLE IF NOT EXISTS usuario_veiculo (
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    placa VARCHAR(50) NOT NULL REFERENCES veiculos(placa) ON DELETE CASCADE,
    PRIMARY KEY (id_usuario, placa)
);