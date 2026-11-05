CREATE TABLE flights (
    carrier TEXT,
    flight_number TEXT,
    origin TEXT,
    destination TEXT,
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    price NUMERIC(10, 2)
);

CREATE INDEX idx_flights_departure_time
ON flights (departure_time);

COPY flights (
    carrier,
    flight_number,
    origin,
    destination,
    departure_time,
    arrival_time,
    price
)
FROM '/docker-entrypoint-initdb.d/flights.csv'
WITH (FORMAT csv, HEADER true, DELIMITER ',');
