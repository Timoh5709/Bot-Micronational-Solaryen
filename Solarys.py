#   Copyright 2025 Timoh5709 (Timoh de Solarys)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from datetime import datetime
import aiohttp
import re
import unicodedata
import json
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Bot connecté en tant que {bot.user}')
    print("Commandes slash synchronisées.")

async def send_error(error: str):
    for timoh in bot.get_all_members():
        if timoh.name == "timoh5709":
            await timoh.send(error)
            return

@bot.tree.command(name="ping", description="Pong !")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("PONG !")

@bot.tree.command(name="help", description="Tu veux de l'aide avec le Bot Micronational Solaryen ?")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Aide pour le Bot Micronational Solaryen",
        description="Voici la liste des commandes disponibles :",
        color=discord.Color.from_rgb(15, 5, 107)
    )
    
    embed.add_field(name="/help", value="Vous donne ce message.", inline=False)
    embed.add_field(name="/ping", value="Permet de tester la présence du bot.", inline=False)
    embed.add_field(name="/infos", value="Donne l'ensemble des annonces du jour.", inline=False)
    embed.add_field(name="/nombre-salon categorie:[Catégorie]", value="Donne le nombre de salons dans une catégorie.", inline=False)
    embed.add_field(name="/search_microwiki query:[Titre de l'article]", value="Donne une liste d'articles du Microwiki ayant pour titre 'query'.", inline=False)
    embed.add_field(name="/search_invites query:[Nom du serveur]", value="Donne les liens d'invitations analysées par le bot.", inline=False)
    embed.add_field(name="/ajouter_bot", value="Vous donne un lien permettant d'ajouter ce bot sur votre serveur.", inline=False)
    
    embed.set_footer(text="Ce bot est sous version 1.0. Si vous voulez contribuer au développement de ce bot micronational, contactez Timoh de Solarys.")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="infos", description="Récupère les liens des annonces envoyées par d'autres serveurs aujourd'hui, regroupées par source.")
async def infos(interaction: discord.Interaction):
    await interaction.response.send_message("Récupération des annonces en cours...")
    
    messages_by_server = {}
    today = datetime.now().date()
    total_channels = len(interaction.guild.text_channels)
    channels_processed = 0
    messages_processed = 0

    for channel in interaction.guild.text_channels:
        async for message in channel.history(limit=None):
            if message.created_at.date() == today:
                if message.flags.is_crossposted:
                    source_server = message.channel.name
                    message_link = message.jump_url

                    if source_server not in messages_by_server:
                        messages_by_server[source_server] = []
                    messages_by_server[source_server].append(message_link)
                    messages_processed += 1
            else:
                break

        channels_processed += 1
        progress_percentage = (channels_processed / total_channels) * 100
        if channels_processed % 5 == 0:
            await interaction.edit_original_response(content=f"Récupération des annonces en cours... {progress_percentage:.2f}% terminé, {messages_processed} annonce(s) trouvée(s).")
    
    embeds = []
    embed = discord.Embed(
        title="Les infos du jour",
        color=discord.Color.from_rgb(15, 5, 107),
        description="Voici les annonces relayées aujourd'hui."
    )

    def embed_size(embed):
        "Calcule la taille totale d'un embed."
        total_size = len(embed.title) + len(embed.description or "")
        for field in embed.fields:
            total_size += len(field.name) + len(field.value)
        return total_size

    for server, links in messages_by_server.items():
        value = ""

        for link in links:
            if len(value) + len(link) + 1 > 1024 or embed_size(embed) + len(value) + len(link) + 1 > 6000:
                embeds.append(embed)
                embed = discord.Embed(
                    title="Les infos du jour (suite)",
                    color=discord.Color.from_rgb(15, 5, 107)
                )
                value = ""

            value += link + "\n"

        if value:
            embed.add_field(name=f"Annonces du salon {server}", value=value, inline=False)

    if embed.fields:
        embeds.append(embed)

    if embeds:
        await interaction.edit_original_response(content=f"Voici les annonces relayées aujourd'hui ({messages_processed}) :", embed=embeds[0])
        for additional_embed in embeds[1:]:
            await interaction.followup.send(embed=additional_embed)
    else:
        await interaction.edit_original_response(content="Aucune annonce relayée ou postée dans un salon d'annonces aujourd'hui.")

@bot.tree.command(name="nombre_salons", description="Compte le nombre de salons dans une catégorie.")
@app_commands.describe(categorie="La catégorie à vérifier.")
async def nombre_salons(interaction: discord.Interaction, categorie: str):
    
    await interaction.response.send_message("Recherche en cours...")
    
    category = discord.utils.get(interaction.guild.categories, name=categorie)
    if not category:
        await interaction.edit_original_response(content=f"# ❌ La catégorie '{categorie}' n'a pas été trouvée.")
        return
    
    nb_salons = len(category.channels)
    
    await interaction.edit_original_response(content=f"# ✅ La catégorie '{categorie}' contient {nb_salons} salons.")


@bot.tree.command(name="search_microwiki", description="Cherche une information sur Microwiki.")
@app_commands.describe(query="L'information que vous souhaitez chercher.")
async def search_microwiki(interaction: discord.Interaction, query: str):
    await interaction.response.send_message("Recherche en cours sur Microwiki...")
    
    url = "https://micronations.wiki/api.php"
    
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": 10
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DiscordBot/1.0; +https://discordapp.com)"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params) as response:
            data = await response.json()

            
            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                await interaction.edit_original_response(content=f"# Aucun résultat trouvé pour '{query}' sur Microwiki.")
                return
            
            def clean_text(text):
                text = re.sub(r'<.*?>', '', text)
                text = re.sub(r'&.*?;', '', text)
                text = re.sub(r'\|.*\n', '', text)
                return text
            
            first_result_title = search_results[0]["title"]
            image_params = {
                "action": "query",
                "format": "json",
                "titles": first_result_title,
                "prop": "pageimages",
                "pithumbsize": 500
            }
            
            async with session.get(url, params=image_params) as image_response:
                image_data = await image_response.json()
                pages = image_data.get("query", {}).get("pages", {})
                thumbnail_url = None
                for page_id, page_info in pages.items():
                    thumbnail_url = page_info.get("thumbnail", {}).get("source")
                    if thumbnail_url:
                        break
            
            embed = discord.Embed(
                title=f"Résultats de la recherche pour '{query}'",
                description="Voici les articles trouvés sur Microwiki :",
                color=discord.Color.from_rgb(15, 5, 107)
            )

            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            
            for result in search_results:
                title = result["title"]
                snippet = clean_text(result["snippet"])
                result_url = f"https://micronations.wiki/wiki/{title.replace(' ', '_')}"
                embed.add_field(
                    name=title,
                    value=f"{snippet}...\n[Lire l'article complet ici]({result_url})",
                    inline=False
                )
            
            await interaction.edit_original_response(content="",embed=embed)


async def update_html():
    try:
        with open("invites_discord.json", "r") as json_file:
            json_data = json.load(json_file)
    except FileNotFoundError:
        print("Erreur : Le fichier 'invites_discord.json' est introuvable.")

    except json.JSONDecodeError:
        print("Erreur : Le fichier 'invites_discord.json' contient une erreur JSON.")

    try:
        with open("template.html", "r") as html_file:
            html_content = html_file.read()
        current_date = datetime.now().strftime("%d/%m/%Y")
        html_content = html_content.replace("<!--Mettre la date-->", current_date)
        json_string = json.dumps(json_data, indent=4)
        html_content = html_content.replace("<!--JSON-->", json_string)

        with open("invites.html", "w") as updated_file:
            updated_file.write(html_content)
    except FileNotFoundError:
        print("Erreur : Le fichier 'template.html' est introuvable.")
    

@bot.tree.command(name="collect_invites", description="Récupère les liens d'invitation Discord dans tous les salons et les enregistre.")
async def collect_invites(interaction: discord.Interaction):
    if  interaction.user.name != "timoh5709":
        await interaction.response.send_message("Seulement Timoh de Solarys peut utiliser cette commande.")
        return
    
    await interaction.response.send_message("Mise à jour des données...")

    invite_data = {}
    existing_links = set()

    try:
        with open("invites_discord.json", "r", encoding="utf-8") as file:
            invite_data = json.load(file)
            existing_links = {link for links in invite_data.values() for link in links}
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    idx2 = 0
    total_links = sum(len(links) for links in invite_data.values())

    updated_invite_data = {}
    for server_name, links in invite_data.items():
        for link in links:
            try:
                invite = await bot.fetch_invite(link)
                current_server_name = normalize_text(invite.guild.name) if invite.guild else "Serveur inconnu"
                if current_server_name not in updated_invite_data:
                    updated_invite_data[current_server_name] = []
                updated_invite_data[current_server_name].append(link)
            except (discord.NotFound, discord.Forbidden):
                continue

            idx2 += 1
            if idx2 % 50 == 0 or idx2 == total_links:
                await interaction.edit_original_response(content=f"Mise à jour des données... {idx2/total_links*100:.2f}% effectué, il reste {total_links - idx2}/{total_links} liens à actualiser")
    
    idx = 0

    for channel in interaction.guild.text_channels:
        try:
            async for message in channel.history(limit=400):
                if "discord.gg" in message.content or "discord.com/invite" in message.content:
                    for match in re.findall(r"(https?://(?:discord\.gg|discord\.com/invite)/[^\s]+)", message.content):
                        if match not in existing_links:
                            try:
                                invite = await bot.fetch_invite(match)
                                server_name = normalize_text(invite.guild.name) if invite.guild else "Serveur inconnu"
                                if server_name not in updated_invite_data:
                                    updated_invite_data[server_name] = []
                                updated_invite_data[server_name].append(match)
                                existing_links.add(match)
                            except discord.NotFound:
                                continue
                            except discord.Forbidden:
                                continue
        except discord.Forbidden:
            continue
        idx = idx +1
        if idx % 30 == 0:
            await interaction.edit_original_response(content=f"Collecte des liens en cours... {idx/len(interaction.guild.text_channels)*100:.2f}% effectué, il reste {len(interaction.guild.text_channels)-idx}/{len(interaction.guild.text_channels)} salons à chercher")

    if not updated_invite_data:
        await interaction.edit_original_response(content="Aucun nouveau lien trouvé.")
        await update_html()
        await interaction.followup.send(content="Voici la page vous permettant de chercher parmis les liens :",file=discord.File("invites.html"))
        return

    with open("invites_discord.json", "w", encoding="utf-8") as file:
        json.dump(updated_invite_data, file, ensure_ascii=False, indent=4)

    await interaction.edit_original_response(
        content=f"Liens collectés et enregistrés dans `invites_discord.json`. Total de serveurs : {len(invite_data)}."
    )
    await update_html()
    await interaction.followup.send(content="Voici la page vous permettant de chercher parmis les liens :",file=discord.File("invites.html"))

def normalize_text(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8").strip()

@bot.tree.command(name="search_invites", description="Recherche des liens d'invitation par nom de serveur.")
@app_commands.describe(query="Le serveur cherché.")
async def search_invites(interaction: discord.Interaction, query: str):
    try:
        with open("invites_discord.json", "r", encoding="utf-8") as file:
            invite_data = json.load(file)
    except FileNotFoundError:
        await interaction.response.send_message("Le fichier `invites_discord.json` est introuvable.", ephemeral=True)
        return
    except json.JSONDecodeError:
        await interaction.response.send_message("Le fichier `invites_discord.json` est corrompu.", ephemeral=True)
        return

    results = {server: links for server, links in invite_data.items() if query.lower() in server.lower()}

    if not results:
        await interaction.response.send_message(f"Aucun serveur correspondant à '{query}' trouvé.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"Résultats pour '{query}'",
        color=discord.Color.from_rgb(15, 5, 107),
        description="Voici les serveurs et leurs liens d'invitation correspondants."
    )

    for server, links in results.items():
        embed.add_field(
            name=f"{server} ({len(links)} lien(s))",
            value="\n".join(links),
            inline=False
        )

    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name="ajouter_bot", description="Obtiens un lien pour ajouter le Bot Micronational Solaryen !")
async def ajouter_bot(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Ajoute le Bot Micronational Solaryen",
        description="Clique sur le lien ci-dessous pour ajouter le bot à ton serveur Discord.",
        color=discord.Color.from_rgb(15, 5, 107)
    )
    embed.add_field(
        name="Lien d'invitation",
        value="[Ajouter le Bot Micronational Solaryen](https://discord.com/oauth2/authorize?client_id=1125826179346219059)",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

token = input("Token du bot : ")
bot.run(token)
