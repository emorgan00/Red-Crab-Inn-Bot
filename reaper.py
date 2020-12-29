#Scripts for running the AOPS game Reaper.
import discord
from replit import db
import time
from datetime import timedelta
from graph import graph
import random

#default parameters
H = 12 #12 hours between reaps
P = 43200 #first to reap 12 hours
BS = 10 #10 seconds between reaps
BP = 120 #first to reap 2 minutes

#send the reaper logo
async def sendLogo(channel):
  await channel.send(file=discord.File("reaper.png"))

#build the leaderboard
def leaderboard(guild):
  temp = []
  server = str(guild.id)
  for key in db.keys():
    if key.startswith(server):
      #[score,user id]
      userID = int(key[len(server)+1:])
      temp.append([db[key][1],userID])
  temp.sort(reverse=True)
  return temp

#determine the modifier to the score (odds provided by kevinmathz)
def getmodifier(game):
  if db[game][3]==0:
    return 1
  d1000 = random.randint(1,1000)
  if d1000 <= 100:
    return 2
  elif d1000 <= 150:
    return 3
  elif d1000 <= 180:
    return 4
  elif d1000 <= 199:
    return 5
  elif d1000 <= 200:
    return 8
  else:
    return 1

#is this a free reap?
def getfree(game):
  if db[game][3]==0:
    return False
  return (random.randint(1,50)==1)

#the begin game message (can be edited later on)
def openingcrawl(game):
  mode = "blitz" if "BLITZ "+game in db.keys() else "standard"
  unit = "seconds" if mode=='blitz' else "hours"
  between = int(3600*db[game][1]) if mode=='blitz' else db[game][1]
  status = "ENABLED" if db[game][3]==1 else "DISABLED"
  return """**The game has begun!**
    - To play, simply type in reap to make your first reap!
    - For the rules and objectives, check out 
    <https://artofproblemsolving.com/reaper>.
    - The time between reaps is {between} {unit}.
    - Reap {delta} ({win} points) to win!
    - This is a {mode} game.
    - Reap modifiers are {status}.
    - Talk to the mods for additional information.
    """.format(between=between,unit=unit,delta=str(timedelta(seconds=db[game][2])),win=db[game][2],mode=mode,status=status)

#End the game
async def endgame(message):
  server = str(message.guild.id)
  game = "REAPER GAME "+server
  blitz = True if "BLITZ "+game in db.keys() else False

  rankList = leaderboard(message.guild)
  champion = 482581806143766529
  if len(rankList)>0:
    champion = rankList[0][1]

  #clear the database of this game's keys
  for key in db.keys():
    if key.startswith(server):
      del db[key]
  del db[game]

  #create a file for final results
  result = "RESULTS"+server+".txt"
  f = open(result,"w+")
  f.write(message.guild.name + " Final Standings: \n")
  for person in rankList:
    member = message.guild.get_member(person[1])
    if member != None:
      f.write(member.name + "#" + member.discriminator + " with " + str(person[0]) + " points\n")
  f.close()

  response = """**The game has ended!**
  - The winner is <@{champion}>!!
  - Final standings are available in the attached file.
  - Talk to the mods for more details.
  """.format(champion=champion)
  
  files = [discord.File(result,filename=message.guild.name + " Final Standings.txt")]

  if blitz:
    events = db["BLITZ "+game]
    del db["BLITZ "+game]
    top = []
    for i in range(0,min(5,len(rankList))):
      top.append(rankList[i][1])
    image = graph(events,message.guild,top)
    files.append(image)

  #send the message and files
  m = await message.channel.send(content=response,files=files)
  try:
    await m.pin()
  except:
    print(m.guild.name + " doesn't have pin privileges")
  await message.channel.edit(slowmode_delay=15)

#The amount of time before you can reap again
def canreap(currentTime,message):
  yourID = str(message.author.id)
  yourInfo = str(message.guild.id) + " " + yourID
  game = "REAPER GAME " + str(message.guild.id)
  if yourInfo not in db.keys() or currentTime-db[yourInfo][0] >= db[game][1]*3600000:
    return ""
  else:
    remaining = int(db[game][1]*3600000-(currentTime-db[yourInfo][0]))
    delta = timedelta(seconds=remaining//1000)
    return str(delta)

def find(text,i):
  f = text.find(' ',i)
  if f==-1:
    return None
  else:
    return f
  
#keys are server id + " " + user id
#values are (time,score) tuples
#gamekey is "REAPER GAME "+server and gamevalue is (current time, time between reaps, points to win, begin-game-message-id)
async def reaper(message):
  #senders info
  response=""
  yourID = str(message.author.id)
  author = message.author.name if message.author.nick == None else message.author.nick
  server = str(message.guild.id)
  channel = message.channel.name
  game = "REAPER GAME "+server
  blitz = True if "BLITZ "+game in db.keys() else False
  yourInfo = server + " " + yourID

  #get the time
  currentTime = int(round(time.time() * 1000))

  #check if the user is an admin
  admin = False
  for role in message.author.roles:
    if role.name == 'reaper-admin':
      admin = True
      break
  #Reaper Test Server Only1
  if message.guild.id==791479138447917076:
    admin = True
  
  #content of the user's message
  text = message.content.lower()

  #begin the game (check parameters)
  if admin and (text.startswith('begin game') or text.startswith('begin blitz game')) and game not in db.keys() and channel=='reaper':
    blitz = True if text.find('blitz') >= 0 else False
    cooldown = H
    towin = P
    random = 1
    if blitz:
      cooldown = BS
      towin = BP
    hi = text.find('h=')
    si = text.find('s=')
    pi = text.find('p=')
    rngi = text.find('rng=')

    try:
      hours = float(text[hi+2:find(text,hi)])
      if not blitz:
        cooldown = min(max(hours,0.003),1000)
    except:
      pass

    try:
      seconds = int(text[si+2:find(text,si)])
      if blitz:
        cooldown = min(max(seconds,5),500)
    except:
      pass
    
    try:
      points = int(text[pi+2:find(text,pi)])
      towin = max(points,10)
      if blitz:
        towin = min(points,5000)
    except:
      pass
    
    try:
      random = int(text[rngi+4:find(text,rngi)])
      if 0 <= random <= 1:
        pass
      else:
        error=1//0
    except:
      pass

    if blitz:
      cooldown = cooldown/3600
    db[game] = (currentTime,cooldown,towin,random,0)
    if blitz:
      db["BLITZ "+game] = [currentTime]
    slowdown = min(21600,int(3600*cooldown))
    await message.channel.edit(slowmode_delay=slowdown)
    await sendLogo(message.channel)
    return openingcrawl(game),True
  #build the help box in markdown
  elif text == 'help':
    response = """For a thorough overview, check out the Github README available here: <https://github.com/Agnimandur/Red-Crab-Inn-Bot>```
Admin (those with the @reaper-admin role):

  begin game h=[h] p=[p] rng=[rng]
  Begin the game! The reap cooldown is [h] hours, and the points to win is [p]. If [rng]=0, reap multipliers and free reaps are disabled. These games will likely take days if not weeks to finish.
  
  begin blitz game s=[s] p=[p] rng=[rng]
  Begin a blitz reaper game! The reap cooldown is [s] seconds. In blitz all participants compete simultaneously from beginning to end. Usually, a blitz game takes between 2 minutes and 2 hours to finish. A fancy results graph is also displayed.

                    
  h=[h]             Change the reap cooldown to [h] hours.
  s=[s]             Change the reap cooldown to [s] seconds.
  p=[p]             Change the points needed to win to [p].
  rng=[rng]         Turn randomness on or off.
  end game          End the game manually.
  reset [users]     Resets the score of all @ed [users].
    
Contestant (these only work in the #reaper or #reaper-discussion channel):
  reap              Reap to gain points! The points are equal to the time
                    difference between your reap and the most recent reap.
                    There is a cooldown, so reap wisely to maximize points!
                    Avoid getting "sniped" and wasting precious reaps.
  timer             The current value of a reap.
  nextreap          The time before you can next reap.
  rank=[name]       Your current rank in the ongoing game. If [name] is given,
                    it finds the scores of aLL players with that [name].
  leaderboard       The current top 10 leaderboard.
    ```
    """
  if game not in db.keys():
    return response,False

  #These commands only work in ongoing games
  #end the game
  if admin and text == 'end game' and channel=='reaper':
    await endgame(message)
  #change the number of hours between reaps or the points needed to win (try/except statements to check valid inputs)
  #update the database (tuples are immutable!)
  elif admin and text.startswith('h=') and channel=='reaper' and not blitz:
    try:
      cooldown = min(max(float(text[2:]),0.003),1000)
      db[game] = (db[game][0],cooldown,db[game][2],db[game][3],db[game][4])
      response = "Reap cooldown updated to {h} hours.".format(h=cooldown)
      beginMessage = await message.channel.fetch_message(db[game][4])
      if beginMessage != None:
        slowdown = min(21600,int(3600*cooldown))
        await message.channel.edit(slowmode_delay=slowdown)
        await beginMessage.edit(content=openingcrawl(game))
    except:
      pass
  elif admin and text.startswith('s=') and channel=='reaper' and blitz:
    try:
      cooldown = min(max(int(text[2:]),5),500)
      db[game] = (db[game][0],cooldown/3600,db[game][2],db[game][3],db[game][4])
      response = "Reap cooldown updated to {s} seconds.".format(s=cooldown)
      beginMessage = await message.channel.fetch_message(db[game][4])
      if beginMessage != None:
        slowdown = min(21600,cooldown)
        await message.channel.edit(slowmode_delay=slowdown)
        await beginMessage.edit(content=openingcrawl(game))
    except:
      pass
  elif admin and text.startswith('p=') and channel=='reaper':
    try:
      towin = max(10,int(text[2:]))
      if blitz:
        towin = min(towin,5000)
      db[game] = (db[game][0],db[game][1],towin,db[game][3],db[game][4])
      response = "Points to win updated to {p} points.".format(p=towin)
      beginMessage = await message.channel.fetch_message(db[game][4])
      if beginMessage != None: 
        await beginMessage.edit(content=openingcrawl(game))
    except:
      pass
  elif admin and text.startswith('rng=') and channel=='reaper':
    try:
      random = int(text[4:])
      if 0 <= random <= 1:
        pass
      else:
        error=1//0
      db[game] = (db[game][0],db[game][1],db[game][2],random,db[game][4])
      response = "Randomness has been {status}.".format(status="ENABLED" if random==1 else "DISABLED")
      beginMessage = await message.channel.fetch_message(db[game][4])
      if beginMessage != None: 
        await beginMessage.edit(content=openingcrawl(game))
    except:
      pass
  elif admin and 'reset' in text:
    for member in message.mentions:
      hisInfo = server + " " + str(member.id)
      if hisInfo in db.keys():
        db[hisInfo] = (0,0)
    response = "Reset successfully completed!"
  elif text=='nextreap':
    nextReap = canreap(currentTime,message)
    if len(nextReap) == 0:
      response = "Hi <@{author}>, your reap is not on cooldown!".format(author=yourID)
    else:
      response = "Hi <@{author}>, you need to wait {delta} before you can next reap.".format(author=yourID,delta=nextReap)
  #reap!
  elif text.startswith('reap') and len(text) <= 6 and channel=='reaper':
    #can't reap
    nextReap = canreap(currentTime,message)
    if len(nextReap) > 0:
      response="Hi <@{author}>, please wait {delta} before reaping again.".format(author=yourID,delta=nextReap)
    else:
      #get scoring info
      modifier = getmodifier(game)
      free = getfree(game)
      score = (modifier*(currentTime - db[game][0]))//1000
      newScore = score
      if yourInfo in db.keys():
        newScore += db[yourInfo][1]
      newTime = 0 if free else currentTime
      
      #send results
      bonus = ""
      if modifier > 1:
        bonus = "You also got a {mod}x reap".format(mod=modifier)
        if free:
          bonus += " and a free reap!!"
        bonus += "!"
      await message.channel.send("Congratulations <@{author}>, your reap earned {score} points.".format(author=message.author.id,score=score)+bonus)

      #update database with your time and score
      try:
        db[game] = (currentTime,db[game][1],db[game][2],db[game][3],db[game][4])
        db[yourInfo] = (newTime,newScore)
        if blitz:
          events = db["BLITZ "+game]
          events.append([currentTime,newScore,int(yourID)])
          db["BLITZ "+game] = events
        response = ""
        #check for a winner
        if newScore >= db[game][2]:
          await endgame(message)
      except:
        pass
  #get the current reap time
  elif text=='timer':
    points = (currentTime - db[game][0])//1000
    response = "The current reap time is {points} seconds.".format(points=points)
  #print out a top10 current leaderboard
  elif text=='leaderboard':
    rankList = leaderboard(message.guild)
    response = "**Reaper Leaderboard**\n"
    i = 0
    for person in rankList:
      if i==min(len(rankList),10):
        break
      #skip people who aren't in the server anymore
      member = message.guild.get_member(person[1])
      if member==None:
        continue
      add = "{pos}. {name} with {points} pts\n".format(pos=i+1,name=member.nick if member.nick != None else member.name,points=person[0])
      response += add
      i += 1
  #get your rank
  elif text=='rank':
    if yourInfo not in db.keys():
      response = "Hi <@{author}>, make a reap to join the game!".format(author=yourID)
    else:
      rankList = [x[1] for x in leaderboard(message.guild)]
      rank = rankList.index(int(yourID))+1
      response = "Hi <@{author}>, your current score is {score} points. Your current rank in the game is {rank} out of {total} players.".format(author=yourID,score=db[yourInfo][1],rank=str(rank),total=str(len(rankList)))
  #find the scores of other people
  elif text.startswith('rank=') and len(text)>9:
    search = message.content[5:]
    #all members whose names start with "search"
    members = await message.guild.query_members(search,limit=5)
    if len(members)>0:
      for member in members:
        hisInfo = server + " " + str(member.id)
        hisName = member.name if member.nick==None else member.nick
        #check if they're in the game or not
        try:
          response += "{name} currently has {score} points.\n".format(name=hisName,score=db[hisInfo][1])
        except:
          response += hisName + " has not reaped in this game yet.\n"
    else:
      response = search+" is not in this server."
  return response,False