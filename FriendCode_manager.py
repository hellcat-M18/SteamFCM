import discord
import discord.app_commands
import MySQLdb
import os
from dotenv import load_dotenv

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

load_dotenv()

client = discord.Client(intents=discord.Intents.default())
Token = os.environ.get("Bot_Token")
tree = discord.app_commands.CommandTree(client)

def mysql_connect():
    connection = MySQLdb.connect(
        user = "root",
        passwd = "061210",
        host = "localhost",
        db = "friend_code_manager"
    )
    cursor = connection.cursor()
    return connection, cursor



with open("private.pem","rb") as file:
  private_pem = file.read()
  private_key = RSA.import_key(private_pem)

with open("public.pem","rb") as file:
  public_pem = file.read()
  public_key = RSA.import_key(public_pem)

cipher_rsa = PKCS1_OAEP.new(public_key)

decipher_rsa = PKCS1_OAEP.new(private_key)


@tree.command(
    name="record",
    description="データを登録します"
)

async def record(interaction:discord.Interaction,username:str,code:str):

    cipher_username = cipher_rsa.encrypt(username.encode())
    cipher_code = cipher_rsa.encrypt(code.encode())

    connection,cursor = mysql_connect()
    connection

    user_id = interaction.user.id

    stmt = "select * from friend_code where discord_user_id = %s"
    cursor.execute(stmt,(user_id,))

    result = cursor.fetchall()

    if len(result) == 0:
        stmt = "insert into friend_code values(%s,%s,%s)"
        cursor.execute(stmt,(user_id,cipher_username,cipher_code))

        embed = discord.Embed(title="登録完了",description="情報を登録しました",color=0x00FF00)
        embed.add_field(name="ユーザー名",value=username,inline = False)
        embed.add_field(name="フレンドコード",value=code,inline = False)


    
    else:
        stmt = "update friend_code set username = %s,code = %s where discord_user_id=%s"
        cursor.execute(stmt,(cipher_username,cipher_code,user_id))

        embed = discord.Embed(title="更新完了",description="情報を更新しました",color=0x0000FF)
        embed.add_field(name="ユーザー名",value=username,inline = False)
        embed.add_field(name="フレンドコード",value=code,inline = False)

    connection.commit()

    cursor.close()
    connection.close()
    


    await interaction.response.send_message(embed = embed)






@tree.command(
    name = "show",
    description= "データを表示します"
)

async def show(interaction:discord.Interaction):
    connection,cursor = mysql_connect()
    connection

    user_id = interaction.user.id

    stmt = "select username,code from friend_code where discord_user_id = %s"
    cursor.execute(stmt,(user_id,))

    result = cursor.fetchall()
    
    if len(result) == 0:
        embed = discord.Embed(title="エラー",description="データが見つかりませんでした\nまずは```/record```でデータを登録しましょう",color=0xFF0000)
        await interaction.response.send_message(embed = embed)
    
    else:
        cipherd_username = result[0][0]
        cipherd_code = result[0][1]

        username = decipher_rsa.decrypt(cipherd_username).decode("UTF-8")
        code = decipher_rsa.decrypt(cipherd_code).decode("UTF-8")


        embed = discord.Embed(title=f"{interaction.user}の情報",description=f"{interaction.user}のユーザー名とフレンドコードです",color=0x00FFFF)
        embed.add_field(name="ユーザー名",value=username)
        embed.add_field(name="フレンドコード",value=code)

        await interaction.response.send_message(embed = embed)
    

    cursor.close()
    connection.close()


@tree.command(
    name = "help",
    description="ヘルプです"
)
async def help(interaction:discord.Interaction):
    embed = discord.Embed(title="ヘルプ",description="コマンド一覧")
    embed.add_field(name="/record",value="ユーザー名とフレンドコードを登録します",inline=False)
    embed.add_field(name="/show",value="登録したフレンドコードを表示します",inline=False)
    embed.add_field(name="/help",value="このヘルプを表示します",inline=False)

    await interaction.response.send_message(embed=embed)



@client.event
async def on_ready():
    print("Discord.py Version:"+discord.__version__)
    print(f"{client.user} にログインしました")
    await tree.sync()


client.run(Token)