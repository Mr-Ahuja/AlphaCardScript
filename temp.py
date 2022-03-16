import pandas as pd

df = pd.read_excel("data.xlsx", sheet_name="Sheet1")
df['Card_No'] = df['Card_No'].astype(str)
data =  df.to_dict('records')
new_data = []
for x in data:
    for i in range(8):
        record = {}
        record['Name1'] = x['Name1']
        record['Email'] = x['Email']
        record['Mobile1'] = x['Mobile1']
        record['Amount'] = 1 if (i%2) == 0 else 2
        print(i,1 if (i%2) == 0 else 2,(i%2),(i%2) == 0)
        record['Card_No'] = x['Card_No']
        record['CVV'] = x['CVV']
        record['Month'] = x['Month']
        record['Year'] = x['Year']
        record['ipin'] = x['ipin']
        new_data.append(record)

pd.DataFrame(new_data).to_excel("newdata.xlsx", index=False)