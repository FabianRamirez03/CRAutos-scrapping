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

select * from Cars Where DateExited is not Null Order By DateExited DESC ;

-- Beginner
-- 1
select * from Cars;
-- 2
Select brand, model, year from cars;
-- 3
Select * from Cars where brand = 'Toyota';
-- 4
Select * from Cars where PriceColones > 10000000;
-- 5
select * from Cars Order By Year DESC;
-- 6 
Select * from Cars where Condition = 'Regular';
-- 7 
Select * from Cars where Model Like '%Civic%';
-- 8
Select Count(*) as totalCars from Cars;
-- 9
Select * from Cars where YEAR(DateEntered) = 2023;
-- 10
Select * from Cars where Transmission = 'Manual';

-- Mid
-- 1
SELECT SUM(PriceColones) as SumaPrecios from Cars;
-- 2
SELECT AVG(PriceColones) as PromedioPrecios, FuelType from Cars GROUP BY FuelType;
-- 3
SELECT COUNT(*) as TotalCondicion, Condition from Cars GROUP BY Condition;
-- 4
SELECT * from Cars where Passengers > 5;
-- 5
SELECT * from Cars
	WHERE Year > 2015
	ORDER BY PriceColones DESC;
-- 6 
SELECT * from Cars where Transmission is Null;
-- 7 
-- 8
SELECT AVG(PriceDollars) as AveragePriceDollars from Cars where PriceDollars is NOT NULL;
