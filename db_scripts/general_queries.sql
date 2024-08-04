select * from Cars 
ORDER BY Id DESC;

SELECT COUNT(*) AS totalRows
FROM Cars;

SELECT COUNT(*) AS EVs
FROM Cars
WHERE FuelType = 'Eléctrico';


select * from Cars
order by PriceColones DESC;

SELECT DateExited, URL from Cars 
WHERE DateExited IS NOT NULL;

UPDATE Cars
SET dateExited = NULL