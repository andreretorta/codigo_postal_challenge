# Código Postal Challenge

Este projeto é dividido em duas fases principais: 

1. Enriquecimento da base de dados fornecida (`cp7_data.csv`).  
2. Desenvolvimento de uma API para acesso aos dados processados.

## Primeira Parte: Enriquecimento da Base de Dados

### Passo 1: Processamento Inicial
- O script `csv_2_db` foi desenvolvido para ler, tratar e transformar o arquivo CSV fornecido (`cp7_data.csv`) em um DataFrame.
- Os dados são processados para integração com a API da **GeoAPI**, visando enriquecer a base com informações de **Concelho** e **Distrito**.
- Após o processamento, os registros são inseridos na tabela **"codigo_postal_base"**:

CREATE TABLE codigo_postal_base (
    id_codigo_postal INT IDENTITY(1,1),
    codigo_postal_clean VARCHAR(65) NOT NULL,
    codigo_postal_baseline VARCHAR(65) NOT NULL,
    concelho VARCHAR(65) NOT NULL,
    distrito VARCHAR(65) NOT NULL
);

#### Problema Identificado
- O CSV inicial contém 280 registros, mas apenas 268 retornaram com sucesso pela API. Os 12 registros restantes resultaram em erro (404 - Não Encontrado).

#### Solução Implementada
- Para gerenciar os registros com erro, foi criada a tabela **"codigo_postal_erro_404"**:


CREATE TABLE codigo_postal_erro_404 (
    id_codigo_postal INT IDENTITY(1,1),
    codigo_postal_clean VARCHAR(65) NOT NULL,
    codigo_postal_baseline VARCHAR(65) NOT NULL
);

Os registros com erro foram populados a partir de uma fonte externa, como um arquivo csv fornecido pela **CTT** contendo códigos postais, distritos e concelhos. Os dados foram tratados e armazenados em uma tabela de parâmetro: **"p_codigo_postal"** utilizando o script "excel_2_db".

### Passo 2: Criação de Tabelas de Referência
#### Tabela de Códigos Postais

CREATE TABLE [dbo].[p_codigo_postal](
    id_codigo_distrito BIGINT NULL,
    CP3 BIGINT NULL,
    CP4 BIGINT NULL,
    Concelho VARCHAR(MAX) NULL,
    codigo_postal_clean BIGINT NULL,
    codigo_postal_baseline VARCHAR(MAX) NULL
);

#### Tabela de Distritos
CREATE TABLE [dbo].[p_codigo_distrito](
    id_codigo_distrito INT NOT NULL,
    distrito VARCHAR(65) NOT NULL
);

INSERT INTO p_codigo_distrito (id_codigo_distrito, distrito) VALUES
(01, 'Aveiro'),
(02, 'Beja'),
(03, 'Braga'),
(04, 'Bragança'),
(05, 'Castelo Branco'),
(06, 'Coimbra'),
(07, 'Évora'),
(08, 'Faro'),
(09, 'Guarda'),
(10, 'Leiria'),
(11, 'Lisboa'),
(12, 'Portalegre'),
(13, 'Porto'),
(14, 'Santarém'),
(15, 'Setúbal'),
(16, 'Viana do Castelo'),
(17, 'Vila Real'),
(18, 'Viseu'),
(31, 'Ilha da Madeira'),
(32, 'Ilha de Porto Santo'),
(41, 'Ilha de Santa Maria'),
(42, 'Ilha de São Miguel'),
(43, 'Ilha Terceira'),
(44, 'Ilha da Graciosa'),
(45, 'Ilha de São Jorge'),
(46, 'Ilha do Pico'),
(47, 'Ilha do Faial'),
(48, 'Ilha das Flores'),
(49, 'Ilha do Corvo');

### Passo 3: Consolidação dos Dados
- Duas **views** foram criadas para organizar os dados:

#### View: Registros com Erros (404)
CREATE VIEW [dbo].[vw_codigo_postal_erro_404] as (
SELECT 
	codigo_postal_clean,
	CONCAT(LEFT(codigo_postal_clean,4),'-',RIGHT(codigo_postal_clean,3)) AS codigo_postal_baseline
FROM [dbo].[codigo_postal_erro_404]
)


Antes da view:
![image](https://github.com/user-attachments/assets/cef94a5b-b02a-4b1c-b67a-0e75575798fe)

Após a view:
![image](https://github.com/user-attachments/assets/4c450f27-4854-4eaf-80f8-b6c46dbc0abc)

#### View: Base Consolidada

ALTER VIEW [dbo].[vw_codigo_postal_base_consolidado] AS
SELECT 
    REPLACE(codigo_postal_baseline, '-', '') AS codigo_postal_clean,
    codigo_postal_baseline,
    concelho,
    distrito
FROM [dbo].[codigo_postal_base]

UNION

SELECT 
    c.codigo_postal_clean,
    c.codigo_postal_baseline,
    UPPER(LEFT(a.Concelho, 1)) + LOWER(SUBSTRING(a.Concelho, 2, LEN(a.Concelho) - 1)) AS concelho,
    b.distrito
FROM [dbo].[p_codigo_postal] a
LEFT JOIN [dbo].[p_codigo_distrito] b ON a.id_codigo_distrito = b.id_codigo_distrito
RIGHT JOIN [dbo].[vw_codigo_postal_erro_404] c ON c.codigo_postal_clean = a.codigo_postal_clean
WHERE b.distrito IS NOT NULL;

Antes da View:
![image](https://github.com/user-attachments/assets/29e9d365-c795-4e9f-9d01-55d08d170e43)

Após a View:
![image](https://github.com/user-attachments/assets/003a7696-6989-452a-85cf-2d64e8636b44)

OBS.: Ficou com 8 registros sem serem identificados.

![image](https://github.com/user-attachments/assets/63b10d0c-8c67-4d00-8763-e0a193d33cee)


### Passo 4: Monitoramento e Automatização
#### Tabelas de Suporte
1. **"Log_Load"**: Registra as operações de carga.
2. **"codigo_postal_base_consolidado"**: Armazena o resultado final consolidado.

#### Procedures Criadas
- **"p_Insert_Log"**: Insere logs de carga.
- **"p_codigo_postal_daily"**: Atualiza os registros diários.
- **"p_daily"**: Executa o processo de carga automaticamente.


  **Insert_Log:**
CREATE PROCEDURE [dbo].[p_Insert_Log] (@id_load bigint, @what nvarchar(128), @obs nvarchar, @dt_ini datetime, @dt_fim datetime, @n_registos_ini bigint, @n_registos_fim bigint) as
BEGIN
    -- Insere na tabela de registro
    INSERT INTO Log_load (id_load, what, obs, dt_ini, dt_fim, n_registos_ini, n_registos_fim)
    VALUES (@id_load, @what, @obs, @dt_ini, @dt_fim, @n_registos_ini, @n_Registos_fim);
END;

  **p_codigo_postal_daily:**

--CREATE SEQUENCE seq_id_load START WITH 1;

CREATE PROCEDURE [dbo].[p_codigo_postal_daily] (@in_id_load BIGINT)
AS
BEGIN
    DECLARE @id_load BIGINT;
    DECLARE @n_registos_ini BIGINT;
    DECLARE @n_registos_fim BIGINT;
	DECLARE @next_id_load BIGINT;

    -- Verificando e somando os valores
    IF @in_id_load IS NOT NULL
        SET @id_load = @in_id_load;
    ELSE
        SET @id_load = NEXT VALUE FOR seq_id_load;
 
    DELETE FROM codigo_postal_base_consolidado;
    SET @n_registos_ini = @@ROWCOUNT;

    DECLARE @currentDateTime DATETIME;
    SET @currentDateTime = GETDATE();

    DECLARE @name nvarchar (128);
    SET @name = 'codigo_postal_base_consolidado';
 
    EXEC p_Insert_Log @id_load, @name , NULL, @currentDateTime, NULL, @n_registos_ini, @n_registos_fim;
 
    INSERT INTO codigo_postal_base_consolidado
    SELECT * FROM vw_codigo_postal_base_consolidado

 
    -- Obter o número de registros na tabela após a inserção
    SET @n_registos_fim = @@ROWCOUNT;
 
    -- Update o n_registros_fim
    UPDATE Log_load
    SET dt_fim = GETDATE(),
        n_registos_fim = @n_registos_fim
    WHERE id = (
            SELECT MAX(id)
            FROM Log_load
        );
END;

  **p_daily:**

ALTER PROCEDURE [dbo].[p_daily]
AS
BEGIN
    DECLARE @id_load BIGINT;
    SET @id_load = NEXT VALUE FOR seq_id_load;
    EXEC [dbo].[p_codigo_postal_daily] @id_load
END;


**Log_Load:**

![image](https://github.com/user-attachments/assets/73a7f364-7259-45b9-8e8d-dc9a8cdacd2a)


**codigo_postal_base_consolidado:**
![image](https://github.com/user-attachments/assets/f3853a2c-6927-47a9-a41d-dd11fd0ad9d9)



---

## Segunda Parte: Desenvolvimento da API

### Ferramenta Utilizada
- Framework: **Flask**

### Rotas Implementadas
1. **Rota: `/codigos_postais`**  
   Retorna todos os registros da tabela `codigo_postal_base_consolidado` em formato JSON.
   
2. **Rota: `/codigos_postais/<codigo>`**  
   Retorna informações de um código postal específico. Caso o código não seja encontrado, é retornado um erro.

#### Exemplos


- **Sucesso**:

 - **Codigo Postal Todos**:
```
  {
    "codigo_postal_baseline": "9020-032",
    "codigo_postal_clean": "9020032",
    "concelho": "Funchal",
    "distrito": "Ilha da Madeira"
  },
  {
    "codigo_postal_baseline": "9020-040",
    "codigo_postal_clean": "9020040",
    "concelho": "Funchal",
    "distrito": "Ilha da Madeira"
  },
  {
    "codigo_postal_baseline": "9020-045",
    "codigo_postal_clean": "9020045",
    "concelho": "Funchal",
    "distrito": "Ilha da Madeira"
  }
  ```
 - **Codigo Postal Único**: 
  ```
  { "codigo_postal": "1000-001", "concelho": "Lisboa", "distrito": "Lisboa" }
  ```
- **Erro**:  
  ```
  { "erro": "Código postal não encontrado" }
  ```

### Considerações
- O código postal pode ser informado com ou sem hífen.

