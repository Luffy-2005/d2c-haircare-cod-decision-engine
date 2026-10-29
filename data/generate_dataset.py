"""
Dataset Generator for D2C Haircare Brand (Shopify COD Orders)
Generates 2,000 realistic past Cash on Delivery (COD) orders with an overall 28% RTO rate,
matching exact Indian e-commerce operational realities.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_orders_dataset(output_path="data/orders_sample.csv", num_orders=2000, seed=42):
    random.seed(seed)
    np.random.seed(seed)

    first_names = [
        "Aarav", "Pooja", "Rohit", "Ananya", "Simran", "Deepak", "Vikram", "Sneha", "Karan", "Priyanka",
        "Rahul", "Neha", "Aditya", "Riya", "Manish", "Kavita", "Suresh", "Ishita", "Abhishek", "Tanvi",
        "Rajesh", "Meera", "Varun", "Sunita", "Harsh", "Divya", "Gaurav", "Nisha", "Amit", "Swati",
        "Siddharth", "Preeti", "Alok", "Komal", "Nikhil", "Shreya", "Pradeep", "Rashmi", "Vishal", "Jyoti"
    ]
    last_names = [
        "Sharma", "Verma", "Kumar", "Iyer", "Kaur", "Patel", "Singh", "Gupta", "Joshi", "Chopra",
        "Reddy", "Mehta", "Yadav", "Nair", "Mishra", "Das", "Bose", "Rao", "Pandey", "Saxena",
        "Malhotra", "Deshmukh", "Chouhan", "Bhatia", "Jain", "Dubey", "Trivedi", "Sengupta", "Pillai", "Shah"
    ]
    fake_names = [
        "asdf", "test user", "qwerty", "none", "xxx", "user", "abc", "asdfghjk", "fake name",
        "na", "test test", "no name", "customer", "dot"
    ]

    # Pincodes & City tiers
    tier1_cities = [
        ("Mumbai", "Maharashtra", ["400001", "400050", "400076", "400092"]),
        ("Delhi", "Delhi", ["110001", "110019", "110024", "110091"]),
        ("Bangalore", "Karnataka", ["560001", "560034", "560068", "560100"]),
        ("Hyderabad", "Telangana", ["500001", "500032", "500081", "500084"]),
        ("Pune", "Maharashtra", ["411001", "411014", "411038", "411057"]),
        ("Chennai", "Tamil Nadu", ["600001", "600028", "600040", "600096"])
    ]
    tier2_cities = [
        ("Jaipur", "Rajasthan", ["302001", "302015", "302020"]),
        ("Lucknow", "Uttar Pradesh", ["226001", "226010", "226024"]),
        ("Indore", "Madhya Pradesh", ["452001", "452010"]),
        ("Ahmedabad", "Gujarat", ["380001", "380015", "380054"]),
        ("Chandigarh", "Punjab", ["160017", "160022"]),
        ("Kochi", "Kerala", ["682001", "682016"])
    ]
    tier3_high_rto = [
        ("Patna", "Bihar", ["800001", "800020", "800026"]),
        ("Ranchi", "Jharkhand", ["834001", "834005"]),
        ("Varanasi", "Uttar Pradesh", ["221001", "221005"]),
        ("Gaya", "Bihar", ["823001"]),
        ("Muzaffarpur", "Bihar", ["842001", "842002"]),
        ("Darbhanga", "Bihar", ["846004"]),
        ("Meerut", "Uttar Pradesh", ["250001", "250002"]),
        ("Aligarh", "Uttar Pradesh", ["202001"])
    ]

    complete_address_templates = [
        "Flat {flat_no}, {building_name}, {road_name}, Near {landmark}",
        "House No {house_no}, Street {street_no}, Sector {sector}, Behind {landmark}",
        "Plot No {plot_no}, {colony_name}, Opposite {landmark}",
        "Room No {room_no}, 3rd Floor, {building_name}, Near {landmark}"
    ]

    hinglish_address_templates = [
        "Makan no {house_no}, {landmark} ke piche wali gali, purani basti",
        "Chauraha ke paas, Gupta general store ke samne, makan number {house_no}",
        "Railway fatak ke samne, shiv mandir ke bagal mein, {colony_name}",
        "Peepal ped ke paas wali gali, gali no {street_no}, ward 12",
        "Police station ke thoda aage, red building ke 2nd floor pe"
    ]

    vague_address_templates = [
        "Near bus stand",
        "Post office ke paas",
        "Ghar pe aake call karna",
        "Main market, dukan ke paas",
        "Ward number 4, village badlapur",
        "Railway station",
        "Near shiv mandir",
        "Just call before coming"
    ]

    gibberish_address_templates = [
        "asdfghjk qwerty",
        "test address please ignore",
        "xyz street house 0",
        "na na na na",
        "123 fake street sample"
    ]

    products = [
        ("Rosemary & Red Onion Hair Oil (200ml)", 399),
        ("Anti-Dandruff Tea Tree Shampoo (300ml)", 499),
        ("Advanced Hair Growth Serum with Redensyl (50ml)", 649),
        ("Deep Nourishing Argan Hair Spa Mask (200g)", 599),
        ("Advanced Hair Growth Serum with Redensyl (50ml)", 649),
        ("Rosemary & Red Onion Hair Oil (200ml)", 399),
        ("Anti-Dandruff Tea Tree Shampoo (300ml)", 499),
        ("Biotin & Keratin Hair Gummies (60 pcs)", 749),
        ("Advanced Hair Growth Serum with Redensyl (50ml)", 649),
        ("Ultimate Anti-Hairfall & Growth Kit (Serum + Oil + Shampoo)", 1199),
        ("Complete Hair Care Regimen Luxury Combo", 1499)
    ]

    records = []
    base_date = datetime(2026, 9, 1)

    for i in range(1, num_orders + 1):
        order_id = f"ORD-{10000 + i}"
        days_offset = random.randint(0, 58)
        seconds_offset = random.randint(0, 86400)
        created_at = base_date + timedelta(days=days_offset, seconds=seconds_offset)

        # Decide order category profile
        # 1. Obvious Fraud/Gibberish (approx 4%)
        # 2. Repeat Customer with good history (approx 25%)
        # 3. Repeat Customer with bad history (approx 6%)
        # 4. First-time buyer with complete address (approx 40%)
        # 5. First-time buyer with Hinglish address (approx 15%)
        # 6. First-time buyer with vague address (approx 10%)
        profile_roll = random.random()

        is_fraud = False
        is_hinglish = False
        is_vague = False
        is_repeat = False

        if profile_roll < 0.04:
            # Obvious Fraud
            is_fraud = True
            customer_name = random.choice(fake_names)
            phone = random.choice(["9999999999", "1234567890", "0000000000", "8888888888", "987654321", "91234"])
            address_text = random.choice(gibberish_address_templates)
            city_info = random.choice(tier3_high_rto)
            pincode = random.choice(["999999", "000000", "123456", city_info[2][0]])
            city, state = city_info[0], city_info[1]
            past_orders = 0
            past_rto = random.choice([0, 1, 2])
            prod, price = random.choice(products)
            order_value = price
            rto_prob = 0.95

        elif profile_roll < 0.29:
            # Repeat customer - Good History
            is_repeat = True
            customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            phone = f"9{random.randint(100000000, 999999999)}"
            city_info = random.choice(tier1_cities + tier2_cities)
            city, state = city_info[0], city_info[1]
            pincode = random.choice(city_info[2])
            address_text = random.choice(complete_address_templates).format(
                flat_no=random.randint(101, 904),
                building_name=f"{random.choice(['Lotus', 'Sunshine', 'Greenwood', 'Galaxy', 'Silver'])} Apartments",
                road_name=f"{random.choice(['MG', 'Link', 'Ring', 'Station', 'Park'])} Road",
                house_no=random.randint(1, 150),
                street_no=random.randint(1, 15),
                sector=random.randint(1, 45),
                colony_name=f"{random.choice(['Adarsh', 'Shanti', 'Vasant', 'Model'])} Nagar",
                landmark=f"{random.choice(['HDFC Bank', 'Apollo Pharmacy', 'City Mall', 'St. Xavier School'])}",
                plot_no=random.randint(10, 80),
                room_no=random.randint(1, 30)
            )
            past_orders = random.randint(1, 6)
            past_rto = 0
            prod, price = random.choice(products)
            order_value = price
            rto_prob = 0.05  # Repeat good customers rarely return

        elif profile_roll < 0.35:
            # Repeat customer - Bad History (Chronic RTO abuser)
            is_repeat = True
            customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            phone = f"8{random.randint(100000000, 999999999)}"
            city_info = random.choice(tier2_cities + tier3_high_rto)
            city, state = city_info[0], city_info[1]
            pincode = random.choice(city_info[2])
            address_text = random.choice(complete_address_templates).format(
                flat_no=random.randint(101, 904),
                building_name="Shree Heights",
                road_name="Main Road",
                house_no=random.randint(1, 150),
                street_no=random.randint(1, 15),
                sector=random.randint(1, 45),
                colony_name="Railway Colony",
                landmark="Civil Hospital",
                plot_no=random.randint(10, 80),
                room_no=random.randint(1, 30)
            )
            past_orders = random.randint(2, 5)
            past_rto = past_orders - random.choice([0, 1])  # 80%+ past orders were RTO
            prod, price = random.choice(products)
            order_value = price
            rto_prob = 0.82

        elif profile_roll < 0.75:
            # First-time buyer - Complete Address
            customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            phone = f"9{random.randint(100000000, 999999999)}"
            city_info = random.choice(tier1_cities * 2 + tier2_cities)
            city, state = city_info[0], city_info[1]
            pincode = random.choice(city_info[2])
            address_text = random.choice(complete_address_templates).format(
                flat_no=random.randint(101, 1404),
                building_name=f"{random.choice(['Royal', 'Palm', 'Sai', 'Krishna', 'Shiv'])} Residency",
                road_name=f"{random.choice(['Airport', 'Bypass', 'Gandhi', 'Temple'])} Road",
                house_no=random.randint(1, 200),
                street_no=random.randint(1, 25),
                sector=random.randint(1, 55),
                colony_name=f"{random.choice(['Indira', 'Rajendra', 'Kalyan', 'Shivaji'])} Nagar",
                landmark=f"{random.choice(['SBI ATM', 'Govt High School', 'Petrol Pump', 'Ganesh Mandir'])}",
                plot_no=random.randint(5, 120),
                room_no=random.randint(1, 40)
            )
            past_orders = 0
            past_rto = 0
            prod, price = random.choice(products)
            order_value = price
            # Baseline COD RTO for standard first-time buyers with good addresses
            rto_prob = 0.17 if city in [c[0] for c in tier1_cities] else 0.24

        elif profile_roll < 0.90:
            # First-time buyer - Hinglish Vernacular Address (Genuine, but local directions)
            is_hinglish = True
            customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            phone = f"7{random.randint(100000000, 999999999)}"
            city_info = random.choice(tier2_cities + tier3_high_rto)
            city, state = city_info[0], city_info[1]
            pincode = random.choice(city_info[2])
            address_text = random.choice(hinglish_address_templates).format(
                house_no=random.randint(1, 120),
                street_no=random.randint(1, 14),
                colony_name=f"{random.choice(['Purana', 'Naya', 'Shanti'])} Mohalla",
                landmark=random.choice(["Shiv Mandir", "Hanuman Mandir", "Railway Fatak", "Water Tank", "Post Office"])
            )
            past_orders = 0
            past_rto = 0
            prod, price = random.choice(products)
            order_value = price
            # Hinglish addresses are genuine but couriers may have slight delivery friction
            rto_prob = 0.28

        else:
            # First-time buyer - Vague / Incomplete Address
            is_vague = True
            customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            phone = f"6{random.randint(100000000, 999999999)}"
            city_info = random.choice(tier3_high_rto + tier2_cities)
            city, state = city_info[0], city_info[1]
            pincode = random.choice(city_info[2])
            address_text = random.choice(vague_address_templates)
            past_orders = 0
            past_rto = 0
            prod, price = random.choice(products)
            order_value = price
            # Very high RTO without door-to-door details
            rto_prob = 0.68

        # High Order Value penalty (>₹1,000 COD orders tend to suffer buyer remorse)
        if order_value >= 1200:
            rto_prob = min(0.92, rto_prob + 0.12)

        # Determine outcome: Delivered or RTO
        status = "RTO" if random.random() < rto_prob else "Delivered"

        records.append({
            "order_id": order_id,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "customer_name": customer_name,
            "customer_phone": phone,
            "customer_email": f"{customer_name.lower().replace(' ', '.')}{random.randint(10, 99)}@gmail.com",
            "shipping_address": address_text,
            "city": city,
            "state": state,
            "pincode": pincode,
            "product_name": prod,
            "order_value": order_value,
            "payment_mode": "COD",
            "past_orders_count": past_orders,
            "past_rto_count": past_rto,
            "is_first_order": 1 if past_orders == 0 else 0,
            "delivery_status": status
        })

    df = pd.DataFrame(records)

    # Calibrate to exact 28.0% RTO if slight random drift
    current_rto_count = (df["delivery_status"] == "RTO").sum()
    target_rto_count = int(round(num_orders * 0.28))
    diff = target_rto_count - current_rto_count

    if diff > 0:
        # Flip Delivered to RTO among higher risk orders (vague or high value first-timer)
        candidates = df[(df["delivery_status"] == "Delivered") & ((df["is_first_order"] == 1) | (df["order_value"] > 700))].index
        flip_indices = np.random.choice(candidates, size=min(diff, len(candidates)), replace=False)
        df.loc[flip_indices, "delivery_status"] = "RTO"
    elif diff < 0:
        # Flip RTO to Delivered among complete address tier-1 orders
        candidates = df[(df["delivery_status"] == "RTO") & (df["city"].isin([c[0] for c in tier1_cities])) & (df["past_rto_count"] == 0)].index
        flip_indices = np.random.choice(candidates, size=min(abs(diff), len(candidates)), replace=False)
        df.loc[flip_indices, "delivery_status"] = "Delivered"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    final_rto_rate = (df["delivery_status"] == "RTO").mean() * 100
    mean_aov = df["order_value"].mean()

    print(f"[Dataset Generation Complete]")
    print(f"Total Orders: {len(df)}")
    print(f"RTO Count: {(df['delivery_status'] == 'RTO').sum()} ({final_rto_rate:.2f}%)")
    print(f"Delivered Count: {(df['delivery_status'] == 'Delivered').sum()} ({100 - final_rto_rate:.2f}%)")
    print(f"Average Order Value: Rs. {mean_aov:.2f} (Target ~Rs. 649)")
    print(f"Saved to: {output_path}")

    return df

if __name__ == "__main__":
    generate_orders_dataset()
