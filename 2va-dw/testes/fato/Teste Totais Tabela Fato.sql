-- 1. Comparação de Totais Financeiros (Origem vs Destino DW)
SELECT 
    'Origem (modelagem.despesa)' AS Base,
    COUNT(*) AS Total_Linhas,
    ROUND(SUM(valor_empenhado), 2) AS Total_Empenhado,
    ROUND(SUM(valor_liquidado), 2) AS Total_Liquidado,
    ROUND(SUM(valor_pago), 2) AS Total_Pago,
    ROUND(SUM(valor_empenhado - valor_pago), 2) AS Saldo_A_Pagar
FROM modelagem.despesa

UNION ALL

SELECT 
    'Destino (dw_despesas.fatodespesa)' AS Base,
    COUNT(*) AS Total_Linhas,
    ROUND(SUM(valorEmpenhado), 2) AS Total_Empenhado,
    ROUND(SUM(valorLiquidado), 2) AS Total_Liquidado,
    ROUND(SUM(valorPago), 2) AS Total_Pago,
    ROUND(SUM(saldoAPagar), 2) AS Saldo_A_Pagar
FROM dw_despesas.fatodespesa;