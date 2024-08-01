-- Drop tables if they exist
IF OBJECT_ID('dbo.CarImages', 'U') IS NOT NULL 
DROP TABLE dbo.CarImages;

IF OBJECT_ID('dbo.Cars', 'U') IS NOT NULL 
DROP TABLE dbo.Cars;

CREATE TABLE Cars (
    Id INT PRIMARY KEY IDENTITY(1,1),   -- Unique identifier for each vehicle
    Brand VARCHAR(50) NOT NULL,         -- Brand of the vehicle
    Model VARCHAR(50) NOT NULL,         -- Model of the vehicle
    Year INT NOT NULL,                  -- Year of the vehicle
    PriceColones DECIMAL(18, 2) NOT NULL,        -- Price in colones
    PriceDollars DECIMAL(18, 2),       -- Price in dollars
    EngineCapacity VARCHAR(50),         -- Engine capacity of the vehicle
    Style VARCHAR(50),                  -- Style of the vehicle
    Passengers INT,                     -- Number of passengers
    FuelType VARCHAR(50) NOT NULL,               -- Type of fuel
    Transmission VARCHAR(50) NOT NULL,           -- Type of transmission
    Condition VARCHAR(50),              -- Condition of the vehicle
    Mileage INT,                        -- Mileage of the vehicle in kilometers
    ExteriorColor VARCHAR(50),          -- Exterior color
    InteriorColor VARCHAR(50),          -- Interior color
    Doors INT,                          -- Number of doors
    TaxesPaid VARCHAR(10),              -- Indicates if taxes have been paid
    NegotiablePrice VARCHAR(10),        -- Indicates if the price is negotiable
    AcceptsVehicle VARCHAR(10),         -- Indicates if another vehicle is accepted
    Province VARCHAR(50),               -- Province where the vehicle is located
    TransferCost DECIMAL(18, 2),       -- Cost of transfer
    Notes VARCHAR(255),                 -- Additional notes about the vehicle
    DateEntered DATE  NOT NULL,                   -- Date of entry of the vehicle record
    DateExited DATE,                    -- Date of exit of the vehicle record
    URL VARCHAR(255)  NOT NULL UNIQUE                   -- URL of the vehicle
);

CREATE TABLE CarImages (
    Id INT PRIMARY KEY IDENTITY(1,1),   -- Unique identifier for each image record
    CarId INT NOT NULL,                  -- Foreign key referencing the Cars table
    ImageUrl1 VARCHAR(255),              -- URL of the first car image
    ImageUrl2 VARCHAR(255),              -- URL of the second car image
    ImageUrl3 VARCHAR(255),              -- URL of the third car image
    ImageUrl4 VARCHAR(255),              -- URL of the fourth car image
    ImageUrl5 VARCHAR(255),              -- URL of the fifth car image
    FOREIGN KEY (CarId) REFERENCES Cars(Id) -- Establishing foreign key relationship
);
