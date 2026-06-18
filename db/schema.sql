-- ============================================================
-- Schema do Banco de Dados - Zona Azul
-- Este arquivo é executado automaticamente pelo PostgreSQL
-- na inicialização do contêner via docker-entrypoint-initdb.d/
-- ============================================================

-- Reset de estado: garante ambiente limpo a cada rebuild com 'docker-compose down -v'
DROP TABLE IF EXISTS transacoes, multas, configuracao, usuario_veiculo, reservas, veiculos, fiscais, usuarios CASCADE;

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY, -- SERIAL: autoincremento gerenciado pelo PostgreSQL
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    saldo NUMERIC(10,2) DEFAULT 0.00
);

-- Tabela de Fiscais (autenticação separada)
CREATE TABLE IF NOT EXISTS fiscais (
    id_fiscal SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    matricula VARCHAR(50) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL
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
    id_veiculo INTEGER NOT NULL REFERENCES veiculos(id_veiculo) ON DELETE CASCADE,  -- FK: integridade referencial com veiculos
    duracao_horas INTEGER NOT NULL DEFAULT 1,
    preco_total NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    criado_em TIMESTAMP DEFAULT NOW(),
    expira_em TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ATIVA'
);

-- Tabela ponte entre usuário e seus veículos (relação N:N)
-- PRIMARY KEY composta: impede que o mesmo usuário vincule a mesma placa duas vezes
CREATE TABLE IF NOT EXISTS usuario_veiculo (
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    placa VARCHAR(50) NOT NULL REFERENCES veiculos(placa) ON DELETE CASCADE,
    PRIMARY KEY (id_usuario, placa)
);

-- Tabela de configuração de preço
CREATE TABLE IF NOT EXISTS configuracao (
    chave VARCHAR(50) PRIMARY KEY,
    valor NUMERIC(10,2) NOT NULL
);
INSERT INTO configuracao (chave, valor) VALUES ('preco_hora', 5.00);

-- Histórico de transações da carteira
CREATE TABLE IF NOT EXISTS transacoes (
    id_transacao SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL, -- 'RECARGA', 'DEBITO_RESERVA', 'PAGAMENTO_MULTA'
    valor NUMERIC(10,2) NOT NULL,
    descricao VARCHAR(200),
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela de Multas
CREATE TABLE IF NOT EXISTS multas (
    id_multa SERIAL PRIMARY KEY,
    id_fiscal INTEGER NOT NULL REFERENCES fiscais(id_fiscal),
    placa VARCHAR(50) NOT NULL,
    motivo VARCHAR(200) NOT NULL, -- 'SEM_RESERVA', 'RESERVA_EXPIRADA'
    valor NUMERIC(10,2) NOT NULL DEFAULT 50.00,
    criado_em TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'PENDENTE' -- 'PENDENTE', 'PAGA'
);