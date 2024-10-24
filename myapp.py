import pymongo
import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
from PIL import Image

# MongoDB client setup
client = pymongo.MongoClient("mongodb+srv://gajendravaradharaju:ghSUVyh41RUyxiGk@cluster0.66l1q.mongodb.net/")
db = client['farmers_market_db']
collection = db['markets']

# Set Streamlit page configuration
logo_path = r"C:\Users\TejasvniKrishnaveni\Downloads\myapp\WhatsApp Image 2024-10-24 at 22.37.33.jpeg"
logo = Image.open(logo_path)

# Display the logo in the sidebar
st.sidebar.image(logo, width=100)
# Load and display logo at the top


# Custom CSS for background and styling
st.markdown("""
    <style>
    .stApp {
        background-color: #e6f2e6; /* Light green background */
    }
    .sidebar .sidebar-content {
        background-color: #4CAF50; /* Green sidebar */
        color: white;
    }
    h1 {
        color: #4CAF50; /* Dark green title */
    }
    .stButton>button {
        background-color: #4CAF50; /* Green button */
        color: white;
    }
    .stTextInput>div>input {
        background-color: #ffffff; /* White input fields */
        color: #000000;
    }
    .stTextArea>div>textarea {
        background-color: #ffffff; /* White text area */
        color: #000000;
    }
    .image-border {
        border: 3px solid #4CAF50; /* Green border for the first image */
        border-radius: 8px;
    }
    .image-paragraph {
        font-size: 14px; /* Smaller font size for paragraphs */
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Load data from MongoDB
def load_farmers_data():
    farmers_list = list(collection.find({}, {'_id': 0}))
    if not farmers_list:
        data = {
            'Farmer': ['John Doe', 'Mary Smith', 'Tom Lee'],
            'Market': ['Farm Fresh Market', 'Green Valley Market', 'Local Roots'],
            'Produce': ['Tomatoes, Potatoes', 'Carrots, Lettuce', 'Strawberries, Cucumbers'],
            'latitude': [37.7749, 37.8044, 37.7749],
            'longitude': [-122.4194, -122.2712, -122.4313]
        }
        farmers_data = pd.DataFrame(data)
        for _, row in farmers_data.iterrows():
            collection.insert_one(row.to_dict())
        return farmers_data
    return pd.DataFrame(farmers_list)

# Add data to MongoDB
def add_market_to_db(farmer_name, market_name, produce_list, lat, lon):
    new_market = {'Farmer': farmer_name, 'Market': market_name, 'Produce': produce_list, 'latitude': lat, 'longitude': lon}
    collection.insert_one(new_market)

# Update existing market in MongoDB
def update_market_in_db(market_name, updated_farmers_name, updated_produce_list, lat, lon):
    collection.update_one({'Market': market_name}, {"$set": {'Farmer': updated_farmers_name, 'Produce': updated_produce_list, 'latitude': lat, 'longitude': lon}})

# Delete market from MongoDB
def delete_market_from_db(market_name):
    collection.delete_one({'Market': market_name})

# Calculate distance between user and farmer's market
def find_nearby_markets(user_location, data, max_distance_km):
    data['Distance (km)'] = data.apply(lambda row: geodesic(user_location, (row['latitude'], row['longitude'])).km, axis=1)
    return data[data['Distance (km)'] <= max_distance_km]

# Function to generate a folium map for all farmers' market locations
def generate_full_map(farmers_data, user_location):
    m = folium.Map(location=user_location, zoom_start=12, tiles='OpenStreetMap')

    for _, row in farmers_data.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['Market']} - {row['Farmer']} \nProduce: {row['Produce']}",
            icon=folium.Icon(color="green", icon="leaf")
        ).add_to(m)
    
    folium.Marker(
        location=user_location,
        popup="Your Location",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

    return m

# Farmer management functions: add, edit, delete
def manage_farmers_data():
    st.header("Manage Farmers Markets")
    farmers_data = load_farmers_data()

    st.subheader("Current Markets")
    st.dataframe(farmers_data)

    # Display the updated map immediately
    folium_map = generate_full_map(farmers_data, (37.7749, -122.4194))  # Default user location
    st_folium(folium_map, width=725, height=500)

    st.subheader("Add a New Market")
    farmer_name = st.text_input("Farmer Name")
    market_name = st.text_input("Market Name")
    produce_list = st.text_area("List your produce (comma separated)", "E.g., Tomatoes, Potatoes")
    market_coordinates = st.text_input("Enter your market's coordinates (Lat, Lon)", "37.7749, -122.4194")

    if st.button("Add Market"):
        if farmer_name and market_name and produce_list and market_coordinates:
            try:
                lat, lon = map(float, market_coordinates.split(','))
                add_market_to_db(farmer_name, market_name, produce_list, lat, lon)
                st.success(f"Market '{market_name}' added successfully!")
                
                # Reload farmers data and update the map
                farmers_data = load_farmers_data()
                folium_map = generate_full_map(farmers_data, (37.7749, -122.4194))
                st_folium(folium_map, width=725, height=500)

            except ValueError:
                st.error("Please enter valid coordinates in the format 'Lat, Lon'.")
        else:
            st.error("Please fill in all fields.")

    st.subheader("Update Existing Market")
    market_to_update = st.selectbox("Select Market to Update", farmers_data['Market'].tolist())

    if market_to_update:
        market_info = farmers_data[farmers_data['Market'] == market_to_update].iloc[0]
        updated_farmers_name = st.text_input("Updated Farmer Name", market_info['Farmer'])
        updated_produce_list = st.text_area("Updated Produce List", market_info['Produce'])
        updated_market_coordinates = st.text_input("Updated Market Coordinates (Lat, Lon)", f"{market_info['latitude']}, {market_info['longitude']}")

        if st.button("Update Market"):
            if updated_farmers_name and updated_produce_list and updated_market_coordinates:
                try:
                    lat, lon = map(float, updated_market_coordinates.split(','))
                    update_market_in_db(market_to_update, updated_farmers_name, updated_produce_list, lat, lon)
                    st.success(f"Market '{market_to_update}' updated successfully!")

                    # Reload farmers data and update the map
                    farmers_data = load_farmers_data()
                    folium_map = generate_full_map(farmers_data, (37.7749, -122.4194))
                    st_folium(folium_map, width=725, height=500)

                except ValueError:
                    st.error("Please enter valid coordinates in the format 'Lat, Lon'.")
            else:
                st.error("Please fill in all fields.")

    st.subheader("Delete Existing Market")
    market_to_delete = st.selectbox("Select Market to Delete", farmers_data['Market'].tolist())

    if st.button("Delete Market"):
        delete_market_from_db(market_to_delete)
        st.success(f"Market '{market_to_delete}' deleted successfully!")

        # Reload farmers data and update the map
        farmers_data = load_farmers_data()
        folium_map = generate_full_map(farmers_data, (37.7749, -122.4194))
        st_folium(folium_map, width=725, height=500)

    st.subheader("Updated Farmer's Market Data")
    st.dataframe(load_farmers_data())

# Main Streamlit app function
def main():
    st.title("Local Farmer's Market Finder")

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select a page", ["Home", "Market Finder", "Manage Farmers", "Contact Us"])
    if page == "Manage Farmers":
        manage_farmers_data()  # Ensure this function is called
    
    elif page == "Contact Us":
        st.header("Contact Us")
        st.markdown("""<p>If you have any questions, feedback, or need assistance, feel free to reach out to us! 
        We value your input and are here to help you find the best local produce. 
        Please leave your message below, and we will get back to you as soon as possible.</p>""", unsafe_allow_html=True)

        # Text box for collecting messages
        message = st.text_area("Your Message", height=150)

        if st.button("Send Message"):
            if message:
                # Implement functionality to save or send the message as needed
                st.success("Your message has been sent successfully!")
                # Optionally, clear the text area after sending
                message = ""
            else:
                st.error("Please enter a message before sending.")


    if page == "Home":
        st.header("Welcome to the Farmer's Market Finder!")

        # Smaller bordered first image
        st.markdown('<div class="image-border" style="border: 2px solid black; display: inline-block; padding: 5px; margin: auto;">', unsafe_allow_html=True)
        st.image(
            "https://media.istockphoto.com/id/1941134987/photo/happy-farmer-selling-organic-strawberries-to-a-client-at-a-farmers-market.jpg?s=612x612&w=0&k=20&c=RRQLLc9g5g8BPzhA8Pk0jxhq2u-Rq_DckVLm8Fzgw4I=",
            use_column_width='auto',
            width=200,
            caption="Happy Farmer Selling Organic Strawberries"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>Farmers' markets provide fresh and locally grown produce directly from the farmers to the community. They support sustainable agriculture and help strengthen local economies. By connecting consumers directly with the growers, these markets create a transparent food supply chain that encourages healthy eating habits.</p>", unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>In addition to offering seasonal fruits and vegetables, farmers' markets often feature artisanal products, such as homemade jams, baked goods, and organic meats. This diversity not only supports local farmers but also promotes entrepreneurship within the community, creating job opportunities and fostering a sense of pride in local production.</p>", unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>Moreover, visiting farmers' markets provides a unique shopping experience. The vibrant atmosphere, filled with the sounds of chatter and live music, allows people to engage with their community, learn about food sources, and appreciate the hard work that goes into sustainable farming practices.</p>", unsafe_allow_html=True)

        # Equal size images for the rest, right-aligned
        st.markdown("<h3>Fresh Fruits and Vegetables</h3>", unsafe_allow_html=True)
        st.markdown('<div style="text-align: right;">', unsafe_allow_html=True)
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSHNk180_1LsfpcntOHz249U4bsVzHN4bLfHQ&s", 
                  use_column_width='auto', width=200, caption="Fresh Fruits and Vegetables")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>Fresh fruits and vegetables are the backbone of any farmers' market. They offer a variety of seasonal produce that promotes healthy eating. Buying these items directly from farmers ensures that the produce is fresh, flavorful, and often picked at peak ripeness, maximizing nutritional value.</p>", unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>Additionally, purchasing fresh produce from farmers' markets helps reduce carbon footprints associated with food transportation. By sourcing food locally, consumers contribute to more sustainable practices that benefit the environment. This eco-conscious approach is increasingly important in today's world.</p>", unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>Supporting local farmers by buying fresh produce also helps preserve agricultural diversity. Farmers grow heirloom varieties and unique crops that might not be available in grocery stores, promoting biodiversity and protecting heritage seeds. This practice contributes to a more resilient food system.</p>", unsafe_allow_html=True)

        st.markdown("<h3>Local Produce Display</h3>", unsafe_allow_html=True)
        st.markdown('<div style="text-align: right;">', unsafe_allow_html=True)
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQisGYvzmxW7GlhbUWA6Com-NC9f1eGz5cqWA&s", 
                  use_column_width='auto', width=200, caption="Local Produce Display")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>A colorful display of local produce encourages people to buy fresh, organic, and nutritious food directly from the growers. The visual appeal of vibrant fruits and vegetables draws in shoppers, making the experience of grocery shopping more enjoyable and engaging.</p>", unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>Moreover, local produce displays are often accompanied by informative signage that highlights the nutritional benefits of each item. This educational aspect empowers consumers to make healthier choices and understand the origins of their food.</p>", unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>Community engagement is further enhanced when local farmers share stories about their produce, farming techniques, and sustainability practices. These interactions create a bond between consumers and producers, fostering a greater appreciation for the food and the effort that goes into its cultivation.</p>", unsafe_allow_html=True)

        st.markdown("<h3>Shopping for Organic Fruits</h3>", unsafe_allow_html=True)
        st.markdown('<div style="text-align: right;">', unsafe_allow_html=True)
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSw0qWgtjzIsUo0GWVq0iOm8fQZbkfVM62kug&s", 
                  use_column_width='auto', width=200, caption="Shopping for Organic Fruits")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>Shopping at farmers' markets allows consumers to connect with the farmers and learn about their farming practices, fostering a sense of community. Organic farming practices prioritize soil health and biodiversity, resulting in fruits that are not only healthier for consumers but also better for the environment.</p>", unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>When consumers choose organic products, they support sustainable agricultural practices that minimize the use of synthetic pesticides and fertilizers. This not only leads to healthier food options but also helps protect local ecosystems and wildlife.</p>", unsafe_allow_html=True)
        st.markdown("<p class='image-paragraph'>Furthermore, organic fruits are often fresher and more flavorful, as they are grown without artificial additives. This commitment to quality and taste creates loyal customers who appreciate the unique flavors and health benefits of organic produce, making farmers' markets a vital part of the local food landscape.</p>", unsafe_allow_html=True)

    elif page == "Market Finder":
        st.header("Find Your Local Farmer's Market")
        user_location = st.text_input("Enter your location (Lat, Lon)", "37.7749, -122.4194")
        max_distance = st.number_input("Max Distance (km)", min_value=1, max_value=100, value=5)
    
    # Button press logic to calculate nearby markets
    if st.button("Find Markets"):
        if user_location:
            try:
                user_lat, user_lon = map(float, user_location.split(','))
                nearby_markets = find_nearby_markets((user_lat, user_lon), load_farmers_data(), max_distance)
                
                # Store the nearby markets and user location in session state
                st.session_state['nearby_markets'] = nearby_markets
                st.session_state['user_lat'] = user_lat
                st.session_state['user_lon'] = user_lon

                if not nearby_markets.empty:
                    st.success(f"Markets within {max_distance} km of your location.")
                else:
                    st.warning("No markets found within that distance.")
            except ValueError:
                st.error("Please enter valid coordinates in the format 'Lat, Lon'.")

    # If nearby markets are available in session state, display the table and map
    if 'nearby_markets' in st.session_state and not st.session_state['nearby_markets'].empty:
        nearby_markets = st.session_state['nearby_markets']
        user_lat = st.session_state['user_lat']
        user_lon = st.session_state['user_lon']

        # Display the table of nearby markets
        st.dataframe(nearby_markets)
        
        # Generate and display the map
        folium_map = folium.Map(location=[user_lat, user_lon], zoom_start=12, tiles='OpenStreetMap')
        
        # Add markers for nearby markets
        for _, row in nearby_markets.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"{row['Market']} - {row['Farmer']} \nProduce: {row['Produce']}",
                icon=folium.Icon(color="green", icon="leaf")
            ).add_to(folium_map)

        # Add a marker for the user's location
        folium.Marker(
            location=[user_lat, user_lon],
            popup="Your Location",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(folium_map)

        # Render the map in Streamlit
        st_folium(folium_map, width=725, height=500)


if __name__ == "__main__":
    main()
