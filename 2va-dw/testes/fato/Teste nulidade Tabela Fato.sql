-- 2. Teste de Nulidade e Integridade de Chaves na Fato
SELECT 
    COUNT(*) AS Linhas_Com_Chaves_Nulas
FROM dw_despesas.fatodespesa
WHERE dataKey IS NULL 
   OR localKey IS NULL 
   OR unidadeGestoraKey IS NULL 
   OR credorKey IS NULL 
   OR classificacaoKey IS NULL 
   OR licitacaoKey IS NULL;