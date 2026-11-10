SET SQL_SAFE_UPDATES = 0;

UPDATE dw_despesas.dimdata 
SET data_id = '1970-01-01 00:00:00' 
WHERE keyData = 0;

SET SQL_SAFE_UPDATES = 1;

SELECT keyData, data_id FROM dw_despesas.dimdata WHERE keyData = 0;