import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def process_data(user_id,name):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(r"D:\React-App\hello_flask\backend\data_entries.csv")

    # Filter the data for the specified user_id
    user_data = df[(df['User ID'] == user_id) & (df['Name'] == name)]

    # Create a pivot table to sum overdue amounts by Name
    if 'Date' not in user_data.columns:
        user_data['Date'] = pd.date_range(start='1/1/2022', periods=len(user_data), freq='D')
    else:
        user_data['Date'] = pd.to_datetime(user_data['Date'])

    # Sort the data by Date
    user_data = user_data.sort_values(by='Date')

    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(user_data['Date'], user_data['Overdue Amount'], marker='o', linestyle='-')
    plt.title('Overdue Amount Over Time')
    plt.xlabel('Date')
    plt.ylabel('Overdue Amount')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot to a BytesIO object
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    # Encode the image to base64
    graph_url = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    return f"data:image/png;base64,{graph_url}"
