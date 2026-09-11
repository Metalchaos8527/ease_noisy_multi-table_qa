six_shot_robust_examples = [{"input": "Question: Show all card type codes and the number of cards in each type.\nExample Tables: <table_name> : Customers_Cards col : card_id | customer_id | card_type_code | card_number | date_valid_from | date_valid_to | other_card_details row 1 : 1 | 14 | Credit | 4560596484842 | 2011-04-17 09:05:28 | 2018-03-07 17:06:19 | 5567915676420343 row 2 : 2 | 9 | Credit | 4859448397570735 | 2012-05-22 02:05:41 | 2018-02-25 15:43:32 | 4539333582760 row 3 : 3 | 6 | Debit | 348237249146948 | 2014-08-01 14:26:45 | 2018-03-24 15:29:00 | 4916210554814\n", 
                            "output": '''**Explanation**: 
        1. **Relevancy between the question and table**: 
        - The question is asking for "all card type codes and the number of cards in each type," which directly relates to the `Customers_Cards` table.
        - The `card_type_code` column in the `Customers_Cards` table is relevant for identifying the different types of card codes.
        - The question also requires counting the number of cards for each type, which involves the `card_id` column in the `Customers_Cards` table.

        2. **Extract operations**:
        - **Grouping**: We need to group the data by `card_type_code` to categorize the cards into their respective types.
        - **Counting**: After grouping, we need to count the number of `card_id` entries within each group to determine the number of cards for each type.

        3. **Extract important entities**:
        - `Customers_Cards.card_type_code` is extracted because it represents the card type codes that need to be listed.
        - `Customers_Cards.card_id` is extracted to perform the counting operation to find out how many cards exist for each type.

        **Operations**: 
        - #o1: Group (by `card_type_code` to categorize cards)
        - #o2: Count (to count `card_id` entries within each type)

        **Extracted Entities**: 
        - #e1: Customers_Cards.card_type_code
        - #e2: Customers_Cards.card_id'''},
        {"input": "Question: List the order id, customer id for orders in Cancelled status, ordered by their order dates.\nExample Tables: <table_name> : Customer_Orders col : order_id | customer_id | order_status_code | order_date row 1 : 1 | 12 | Completed | 2018-02-10 15:44:48 row 2 : 2 | 4 | New | 2018-01-31 17:49:18 row 3 : 3 | 1 | PartFilled | 2018-02-26 12:39:33\n",
         "output": '''**Explanation**:
1. **Relevancy Between the Question and Table**:
   - The question requests a list of order IDs and customer IDs for orders with a "Cancelled" status. This directly relates to the 'Customer_Orders' table, specifically the 'order_status_code' column, which needs to be filtered to find orders with this status.
   - Additionally, the results should be arranged by the order dates, indicating the need to sort based on the 'order_date' column.

2. **Extract Operations**:
   - **Select and Filter**: Extract the 'order_id' and 'customer_id' columns from the table and filter them to include only entries where 'order_status_code' is "Cancelled".
   - **Sort**: Subsequently, the results need to be ordered by the 'order_date', which implies a sorting operation.

3. **Extract Important Entities**:
   - 'Customer_Orders.order_id' is required because the question asks for a list of order IDs.
   - 'Customer_Orders.customer_id' needs to be extracted as the question asks for customer IDs associated with the orders.
   - 'Customer_Orders.order_status_code' is crucial to filter out only those entries with a "Cancelled" status.
   - 'Customer_Orders.order_date' is essential for sorting the results by the order dates.

**Operations**:
- #o1: Select (to extract `order_id` and `customer_id`)
- #o2: Filter (to filter data where`order_status_code` is "Cancelled")
- #o3: Sort (to order by `order_date`)

**Extracted Entities**:
- #e1: Customer_Orders.order_id
- #e2: Customer_Orders.customer_id
- #e3: Customer_Orders.order_status_code
- #e4: Customer_Orders.order_date'''},
                {"input": "Question: What are the names of tourist attractions that can be reached by bus or is at address 254 Ottilie Junction?\nExample Tables: <table_name> : Locations col : Location_ID | Location_Name | Address | Other_Details row 1 : 333 | Astro Orbiter | 660 Shea Crescent |  row 2 : 368 | African Animals | 254 Ottilie Junction |  row 3 : 417 | American Adventure | 53815 Sawayn Tunnel Apt. 297 |\n<table_name> : Tourist_Attractions col : Tourist_Attraction_ID | Attraction_Type_Code | Location_ID | How_to_Get_There | Name | Description | Opening_Hours | Other_Details row 1 : 2113 | 2 | 579 | bus | art museum |  |  |  row 2 : 2701 | 6 | 417 | walk | UK gallery |  |  |  row 3 : 5076 | 2 | 868 | shuttle | flying elephant |  |  | \n",
                "output": '''**Explanation**: 
        1. **Relevancy between the question and tables**: 
        - The question is asking for the names of tourist attractions, which directly relates to the 'Tourist_Attractions' table, specifically the 'Name' column.
        - The question also mentions reaching the attractions by bus or being at a specific address. The 'How_to_Get_There' column in the 'Tourist_Attractions' table is relevant for determining if an attraction can be reached by bus.
        - The 'Address' column in the 'Locations' table is relevant for checking if the address is "254 Ottilie Junction". The 'Location_ID' column in both tables can be used to join these tables to find the address of each tourist attraction.

        2. **Extract operations**:
        - **Filtering**: We need to filter tourist attractions based on two conditions: those that can be reached by bus and those located at the address "254 Ottilie Junction".
        - **Logical OR operation**: The question specifies "or", so we need to apply a logical OR operation between the two conditions.
        - **Join operation**: A join operation between the 'Tourist_Attractions' and 'Locations' tables is necessary to match the 'Location_ID' and retrieve the address information.

        3. **Extract important entities**:
        - 'Tourist_Attractions.Name' is extracted because the question asks for the names of the tourist attractions.
        - 'Tourist_Attractions.How_to_Get_There' is extracted to determine if the attraction can be reached by bus.
        - 'Locations.Address' is extracted to check if the address is "254 Ottilie Junction".
        - 'Locations.Location_ID' and 'Tourist_Attractions.Location_ID' are extracted to perform the join operation between the two tables.

        **Operations**: 
         - #o1: Join (between `Tourist_Attractions` and `Locations` using `Location_ID`)
         - #o2: Filter (to filter data where`How_to_Get_There' is bus)
         - #o3: Filter (to filter data where Address' includes "254 Ottilie Junction")
         - #o4: Logical OR (between accessibility by bus or address includes "254 Ottilie Junction")

        **Extracted Entities**: 
        - #e1: Tourist_Attractions.Name
        - #e2: Tourist_Attractions.How_to_Get_There
        - #e3: Locations.Address
        - #e4: Locations.Location_ID
        - #e5: Tourist_Attractions.Location_ID'''},
        {"input": "Question: Find the names of the artists who are from Bangladesh and have never received rating higher than 7.\nExample Tables: <table_name> : artist col : artist_name | country | gender | preferred_genre row 1 : Shrikanta | India | Male | tagore row 2 : Prity | Bangladesh | Female | nazrul row 3 : Farida | Bangladesh | Female | folk \n<table_name> : song col : song_name | artist_name | country | f_id | genre_is | rating | languages | releasedate | resolution row 1 : Tumi robe nirobe | Shrikanta | India | 1 | tagore | 8 | bangla | 28-AUG-2011 | 1080 row 2 : Shukno patar nupur pae | Prity | Bangladesh | 2 | nazrul | 5 | bangla | 21-SEP-1997 | 512 row 3 : Ami opar hoye | Farida | Bangladesh | 3 | folk | 7 | bangla | 7-APR-2001 | 320 \n",
         "output": '''**Explanation**: 
1. **Relevancy between the question and tables**: 
   - The question asks for the names of artists from Bangladesh who have never received a rating higher than 7. 
   - The `artist` table contains the `artist_name` and `country`, which are relevant for identifying artists from Bangladesh.
   - The `song` table contains `artist_name`, `country`, and `rating`, which are relevant for checking the ratings of songs by these artists.

2. **Extract Operations**:
   - **Filter**: We need to filter artists based on their `country` being Bangladesh.
   - **Join**: We need to join the table between artist and song by artist_name.
   - **Comparison**: We need to perform a comparison operation to check if the rating is higher than 7. 
   - **Select**: We need to select the `artist_name` if the artist has never received a rating higher than 7.  

3. **Extract Important Entities**:
   - From the `artist` table, the relevant columns are `artist_name` and `country`.
   - From the `song` table, the relevant columns are `artist_name` and `rating`.
   - The entity "Bangladesh" is relevant as it is used to filter the `country` column.
   - The rating value "7" is relevant for the comparison operation.

**Operations**: 
- #o1: Filter (to filter data where `country` is Bangladesh)
- #o2: Join (between `artist` and `song` using `artist_name`)
- #o3: Compare (to check if `rating` is higher than 7)
- #o4: Select (to get `artist_name` with no rating higher than 7)

**Extracted Entities**: 
- #e1: artist.artist_name
- #e2: artist.country
- #e3: song.artist_name
- #e4: song.rating'''},
                    {"input": "Question: Find the name of the storm that affected both Afghanistan and Albania regions.\nExample Tables: <table_name> : storm col : Storm_ID | Name | Dates_active | Max_speed | Damage_millions_USD | Number_Deaths row 1 : 1 | One | May19â\x80\x93May25 | 995 | 13.0 | 0 row 2 : 2 | Two | August3â\x80\x93August10 | 972 | 10.75 | 7 row 3 : 3 | Three | August5â\x80\x93August14 | 972 | 13.0 | 52 \n<table_name> : region col : Region_id | Region_code | Region_name row 1 : 1 | AF | Afghanistan row 2 : 2 | AL | Albania row 3 : 3 | DZ | Algeria \n<table_name> : affected_region col : Region_id | Storm_ID | Number_city_affected row 1 : 1 | 1 | 10 row 2 : 2 | 1 | 15 row 3 : 3 | 3 | 30 \n",
                    "output": '''**Explanation**:
        1. **Relevancy between the question and tables**:
        - The question asks for the name of the storm that affected both Afghanistan and Albania, which involves identifying storms linked to these regions.
        - The `region` table is relevant for identifying the `Region_id` of "Afghanistan" and "Albania" using the `Region_name` column.
        - The `affected_region` table is crucial for linking regions to storms through the `Region_id` and `Storm_ID` columns.
        - The `storm` table is necessary to retrieve the `Name` of the storm using the `Storm_ID`.

        2. **Extract operations**:
        - **Filter**: We need to filter the `region` table to find the `Region_id` for "Afghanistan" and "Albania".
        - **Join**: A join operation is required between the `region` and `affected_region` tables using `Region_id` to link regions to storms.
        - **Comparison**: We need to compare and find common `Storm_ID` entries in the `affected_region` table that affect both regions.
        - **Join**: Another join operation is needed between the `storm` and `affected_region` tables using `Storm_ID` to retrieve the storm's name.
        - **Retrieve**: Finally, we retrieve the `Name` of the storm from the `storm` table.

        3. **Extract important entities**:
        - `region.Region_name` is extracted to identify the regions "Afghanistan" and "Albania".
        - `region.Region_id` is extracted to link region to affected_region.
        - `affected_region.Region_id` is extracted to link regions to storms.
        - `affected_region.Storm_ID` is extracted to find common storms affecting both regions.
        - `storm.Storm_ID` is extracted to link the storm to affected_region.
        - `storm.Name` is extracted to retrieve the name of the storm.

        **Operations**:
        - #o1: Filter (to find `Region_id` for Afghanistan and Albania)
        - #o2: Join (to link `region` and `affected_region` tables using `Region_id`)
        - #o3: Compare (to find common `Storm_ID` affecting both Afghanistan and Albania)
        - #o4: Join (to link `storm` and `affected_region` tables using `Storm_ID`)
        - #o5: Retrieve (to get the `Name` of the storm)

        **Extracted Entities**:
        - #e1: region.Region_name
        - #e2: region.Region_id
        - #e3: affected_region.Region_id
        - #e4: affected_region.Storm_ID
        - #e5: storm.Storm_ID
        - #e6: storm.Name'''},
        {"input": '''Question: Find the titles of all the papers written by "Jeremy Gibbons"\nExample Tables: <table_name> : Authors col : authID | lname | fname row 1 : 50 | Gibbons | Jeremy row 2 : 51 | Hinze | Ralf row 3 : 52 | James | Daniel W. H. \n<table_name> : Papers col : paperID | title row 1 : 200 | Just do it: Simple Monadic Equational Reasoning row 2 : 201 | Proving the Unique Fixed-Point Principle Correct: An Adventure with Category Theory row 3 : 202 | Functional Pearl: Modular Rollback through Control Logging \n<table_name> : Authorship col : authID | instID | paperID | authOrder row 1 : 50 | 1000 | 200 | 1 row 2 : 51 | 1000 | 200 | 2 row 3 : 51 | 1000 | 201 | 1 \n''',
         "output": '''**Explanation**:
1. **Relevancy Between the Question and Tables**:
   - The question is focused on finding the titles of papers written by "Jeremy Gibbons". This involves linking authors to their papers through various tables and columns.
   - Relevant tables include "Authors", "Authorship", and "Papers".
   - In the "Authors" table, the columns 'authID', 'lname', and 'fname' are particularly relevant for identifying "Jeremy Gibbons" by matching 'fname' with "Jeremy" and 'lname' with "Gibbons".
   - In the "Authorship" table, the columns 'authID' and 'paperID' are important for establishing the relationship between the author and their papers.
   - In the "Papers" table, 'paperID' and 'title' are relevant for retrieving the titles of the papers authored by "Jeremy Gibbons".

2. **Extract Operations**:
   - **Matching**: Identify the 'authID' of "Jeremy Gibbons" by matching 'fname' and 'lname' in the "Authors" table.
   - **Joining**: Use the 'authID' obtained from the "Authors" table to join with the "Authorship" table and extract the associated 'paperID'.
   - **Selection**: Finally, select the 'title' from the "Papers" table using the 'paperID' obtained from the "Authorship" table.

3. **Extract Important Entities**:
   - 'Authors.authID' is necessary to connect the author to their papers.
   - 'Authors.lname' and 'Authors.fname' are used to identify "Jeremy Gibbons".
   - 'Authorship.authID' and 'Authorship.paperID' help link the author with their papers.
   - 'Papers.paperID' and 'Papers.title' are crucial for retrieving the titles of the papers associated with the identified 'authID'.

**Operations**:
- #o1: Match (to identify `authID` of "Jeremy Gibbons" using `fname` and `lname`)
- #o2: Join (between `Authors` and `Authorship` using `authID` to extract `paperID`)
- #o3: Select (to get `title` from `Papers` using `paperID`)

**Extracted Entities**:
- #e1: Authors.authID
- #e2: Authors.lname
- #e3: Authors.fname
- #e4: Authorship.authID
- #e5: Authorship.paperID
- #e6: Papers.paperID
- #e7: Papers.title'''}]