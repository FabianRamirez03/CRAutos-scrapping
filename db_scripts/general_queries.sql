select * from Cars

SELECT COUNT(*) AS totalRows
FROM Cars;

SELECT COUNT(*) AS EVs
FROM Cars
WHERE FuelType = 'Eléctrico';


select * from Cars
order by PriceColones DESC;
