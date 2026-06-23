# 数据字典 (Data Dictionary)

> Phase 0 自动生成的骨架,请逐步补全『含义』列。

## DataCo Supply Chain

| 列名 | 类型 | 含义 |
|---|---|---|
| `type` | VARCHAR | Type of transaction made |
| `days_for_shipping_real` | BIGINT | Actual shipping days of the purchased product |
| `days_for_shipment_scheduled` | BIGINT | Days of scheduled delivery of the purchased product |
| `benefit_per_order` | DOUBLE | Earnings per order placed |
| `sales_per_customer` | DOUBLE | Total sales per customer made per customer |
| `delivery_status` | VARCHAR | Delivery status of orders: Advance shipping , Late delivery , Shipping canceled , Shipping on time |
| `late_delivery_risk` | BIGINT | Categorical variable that indicates if sending is late (1), it is not late (0). |
| `category_id` | BIGINT | Product category code |
| `category_name` | VARCHAR | Description of the product category |
| `customer_city` | VARCHAR | City where the customer made the purchase |
| `customer_country` | VARCHAR | Country where the customer made the purchase |
| `customer_email` | VARCHAR | Customer's email |
| `customer_fname` | VARCHAR | Customer name |
| `customer_id` | BIGINT | Customer ID |
| `customer_lname` | VARCHAR | Customer lastname |
| `customer_password` | VARCHAR | Masked customer key |
| `customer_segment` | VARCHAR | Types of Customers: Consumer , Corporate , Home Office |
| `customer_state` | VARCHAR | State to which the store where the purchase is registered belongs |
| `customer_street` | VARCHAR | Street to which the store where the purchase is registered belongs |
| `customer_zipcode` | DOUBLE | Customer Zipcode |
| `department_id` | BIGINT | Department code of store |
| `department_name` | VARCHAR | Department name of store |
| `latitude` | DOUBLE | Latitude corresponding to location of store |
| `longitude` | DOUBLE | Longitude corresponding to location of store |
| `market` | VARCHAR | Market to where the order is delivered : Africa , Europe , LATAM , Pacific Asia , USCA |
| `order_city` | VARCHAR | Destination city of the order |
| `order_country` | VARCHAR | Destination country of the order |
| `order_customer_id` | BIGINT | Customer order code |
| `order_date_date_orders` | VARCHAR | Date on which the order is made |
| `order_id` | BIGINT | Order code |
| `order_item_cardprod_id` | BIGINT | Product code generated through the RFID reader |
| `order_item_discount` | DOUBLE | Order item discount value |
| `order_item_discount_rate` | DOUBLE | Order item discount percentage |
| `order_item_id` | BIGINT | Order item code |
| `order_item_product_price` | DOUBLE | Price of products without discount |
| `order_item_profit_ratio` | DOUBLE | Order Item Profit Ratio |
| `order_item_quantity` | BIGINT | Number of products per order |
| `sales` | DOUBLE | Value in sales |
| `order_item_total` | DOUBLE | Total amount per order |
| `order_profit_per_order` | DOUBLE | Order Profit Per Order |
| `order_region` | VARCHAR | Region of the world where the order is delivered :  Southeast Asia ,South Asia ,Oceania ,Eastern Asia, West Asia , West of USA , US Center , West Africa, Central Africa ,North Africa ,Western Europe ,Northern , Caribbean , South America ,East Africa ,Southern Europe , East of USA ,Canada ,Southern Africa , Central Asia ,  Europe , Central America, Eastern Europe , South of  USA |
| `order_state` | VARCHAR | State of the region where the order is delivered |
| `order_status` | VARCHAR | Order Status : COMPLETE , PENDING , CLOSED , PENDING_PAYMENT ,CANCELED , PROCESSING ,SUSPECTED_FRAUD ,ON_HOLD ,PAYMENT_REVIEW |
| `order_zipcode` | DOUBLE |  |
| `product_card_id` | BIGINT | Product code |
| `product_category_id` | BIGINT | Product category code |
| `product_description` | DOUBLE | Product Description |
| `product_image` | VARCHAR | Link of visit and purchase of the product |
| `product_name` | VARCHAR | Product Name |
| `product_price` | DOUBLE | Product Price |
| `product_status` | BIGINT | Status of the product stock :If it is 1 not available , 0 the product is available |
| `shipping_date_date_orders` | VARCHAR | Exact date and time of shipment |
| `shipping_mode` | VARCHAR | The following shipping modes are presented : Standard Class , First Class , Second Class , Same Day |

## NYC TLC Trip Records

| 列名 | 类型 | 含义 |
|---|---|---|
| `vendor_id` | INTEGER |  |
| `tpep_pickup_datetime` | TIMESTAMP |  |
| `tpep_dropoff_datetime` | TIMESTAMP |  |
| `passenger_count` | DOUBLE |  |
| `trip_distance` | DOUBLE |  |
| `ratecode_id` | DOUBLE |  |
| `store_and_fwd_flag` | VARCHAR |  |
| `pu_location_id` | INTEGER |  |
| `do_location_id` | INTEGER |  |
| `payment_type` | BIGINT |  |
| `fare_amount` | DOUBLE |  |
| `extra` | DOUBLE |  |
| `mta_tax` | DOUBLE |  |
| `tip_amount` | DOUBLE |  |
| `tolls_amount` | DOUBLE |  |
| `improvement_surcharge` | DOUBLE |  |
| `total_amount` | DOUBLE |  |
| `congestion_surcharge` | DOUBLE |  |
| `airport_fee` | DOUBLE |  |

## Taxi Zones

| 列名 | 类型 | 含义 |
|---|---|---|
| `location_id` | BIGINT |  |
| `borough` | VARCHAR |  |
| `zone` | VARCHAR |  |
| `service_zone` | VARCHAR |  |
