##############################################################################
# -*- coding: utf-8 -*-
# By AddonBrasil - 02/10/2015
##############################################################################

import urllib, urllib2, re, xbmcplugin, xbmcgui, xbmc, xbmcaddon, os, time
import json

from resources.lib import control
from resources.lib import client
from resources.lib import jsunpack
from resources.lib import captcha
from resources.lib.BeautifulSoup import BeautifulSoup

addon_id    = 'plugin.video.cinecult'
selfAddon   = xbmcaddon.Addon(id=addon_id)
datapath    = xbmc.translatePath(selfAddon.getAddonInfo('profile'))
addonfolder = selfAddon.getAddonInfo('path')

icon   = addonfolder + '/icon.png'
fanart = addonfolder + '/fanart.jpg'

base   = 'http://tocadoscinefilos.net.br/'
imgsrv = 'http://cinecult.addonbrasil.tk/imgs/'

try    : os.mkdir(datapath)
except : pass

##############################################################################

def menuPrincipal():
		addDir('Filmes'       , base,  10, imgsrv + '_filmes.png')
		addDir('Gêneros'      , base,  20, imgsrv + '_generos.png')
		addDir('Décadas'      , base,  20, imgsrv + '_decadas.png')
		addDir('Países'       , base,  20, imgsrv + '_paises.png')
		addDir('Pesquisar'    , base,  30, imgsrv + '_pesquisa.png')
		addDir('Configurações', base, 999, imgsrv + '_config.png', False)

		setViewMenu()
		
def getMenus(url, name):
		link = openURL(url)
		soup = BeautifulSoup(link)
		conteudo = soup("div", {"class" : "primarymenu"})
		
		listaMenus = conteudo[0]("ul", {"class": "sub-menu"} )
		
		if   name == 'Gêneros' : temp = listaMenus[2]
		elif name == 'Décadas' : temp = listaMenus[1]
		elif name == 'Países'  : temp = listaMenus[0]
		
		menus = temp("li")
		
		totMenus = len(menus)
		
		for item in menus:
				titM = item.text.encode('utf-8', 'ignore')
				urlM = item.a["href"]
				
				if name == "Gêneros" : imgM = imgsrv + '_cc.png'
				else                 : imgM = imgsrv + getImg(titM)
				
				addDir(titM, urlM, 10, imgM, totMenus, True)				

		setViewMenu()
		
def getFilmes(url):
		link  = openURL(url)
		soup  = BeautifulSoup(link)
		
		conteudo = soup("section", {"class": "film-wp"})
		filmes   = conteudo[0]("article", {"class": "film"})
		
		totFilmes = len(filmes)
		
		for filme in filmes:
				titF = filme.img["alt"].encode('utf-8', 'ignore')
				urlF = filme.a["href"]
				imgF = filme.img["src"] 
				addDir(titF, urlF, 100, imgF, False, totFilmes)
				
		try :
				proximas = re.findall('<link rel="next" href="(.*?)" />', link)		
		except :
				proximas = re.findall('<li class="burada"><a href=".*?">.*?</a></li> <li><a href="(.*?)">.*?</a></li>', link)
				
		for proxima in proximas:
				addDir('Próxima Página >>', proxima, 10, imgsrv + '_proxima.png')
				break
				
		setViewFilmes()

def doPlay(url, name):
		nomefilme = name
		
		msgDialog = xbmcgui.DialogProgress()

		msgDialog.create('CINE CULT', 'Buscando Servidores', name, 'Por favor aguarde...')
		msgDialog.update(25)
		
		link = openURL(url)
		
		msgDialog.update(50, 'Resolvendo Servidores', name, 'Por favor aguarde...')
		
		servidores = []
		links      = []
		
		try :
				url2Rslv = re.findall('src="https://openload.co/splash/(.*?)/.*?"', link)[0]
				url2Rslv = 'https://openload.co/embed/' + url2Rslv
				
				servidores.append('OPENLOAD')
				links.append(url2Rslv)
		except :
				pass
				
		try :
				url2Rslv = re.findall('src="http://vidzi.tv/embed-(.*?)-.*?"', link)[0]
				url2Rslv = 'http://vidzi.tv/' + url2Rslv + '.html'
				
				servidores.append('VIDZI')
				links.append(url2Rslv)
		except:
				try :
						url2Rslv = re.findall('SRC="http://vidzi.tv/embed-(.*?)-.*?"', link)[0]
						url2Rslv = 'http://vidzi.tv/' + url2Rslv + '.html'
						
						servidores.append('VIDZI')
						links.append(url2Rslv)
				except:
						pass
				
		if not servidores : return
		
		totServs = len(servidores)
		
		if  totServs > 1 : index = xbmcgui.Dialog().select('Selecione um dos servidores suportados :', servidores)
		else             : index = 0

		if index == -1 : return

		urlVideo = links[index]
		
		if   'openload'  in urlVideo : url2Play = getOpenLoad(urlVideo)
		elif 'vidzi.tv'  in urlVideo : url2Play = getVidzi(urlVideo)
				
		msgDialog.update(75, 'Abrindo Sinal', name, 'Por favor aguarde...')
		
		urlVideo   = url2Play[0]
		urlLegenda = url2Play[1]
		
		if urlVideo:
				playlist = xbmc.PlayList(1)
				playlist.clear()
		
				liz = xbmcgui.ListItem(nomefilme, iconImage=iconimage, thumbnailImage=iconimage)
				liz.setInfo(type="Video", infoLabels={ "Title": name })
				liz.setPath(urlVideo)
				liz.setProperty('mimetype', 'video/mp4')
				liz.setProperty('IsPlayable', 'true')
				
				msgDialog.update(100)

				playlist.add(urlVideo, liz)
				xbmcPlayer = xbmc.Player(xbmc.PLAYER_CORE_AUTO)
				xbmcPlayer.play(playlist)
				
				if urlLegenda != '-':
						if 'timedtext' in urlLegenda :
								import os.path
								sfile = os.path.join(xbmc.translatePath("special://temp"),'sub.srt')
								sfile_xml = os.path.join(xbmc.translatePath("special://temp"),'sub.xml')
								sub_file_xml = open(sfile_xml,'w')
								sub_file_xml.write(urllib2.urlopen(urlLeg).read())
								sub_file_xml.close()
								print "Sfile.srt : " + sfile_xml
								xmltosrt.main(sfile_xml)
								xbmc.sleep(1000)
								xbmcPlayer.setSubtitles(sfile)
						else:
								xbmcPlayer.setSubtitles(urlLegenda)
				else :
						try :
								urlLegenda = re.findall('href="(.*?)">Legenda', link)[0]
								
								xbmc.sleep(1000)
								xbmcPlayer.setSubtitles(urlLegenda)
						except :
								pass
				
		else:
				msgDialog.update(100)
				dialog = xbmcgui.Dialog()
				dialog.ok("CINE CULT", "Filme Indisponível", "Este filme ainda não esta disponível...", "Tente novamente em breve.")		
				
def getOpenLoad(url):
		link = client.request(url)
		
		try :
				leg = re.findall('<track kind="captions" src="(.*?)"', link)[0]
				urlLegenda = 'https://openload.co' + str(leg)
		except :
				urlLegenda = '-'
				
		id = re.compile('//.+?/(?:embed|f)/([0-9a-zA-Z-_]+)').findall(url)[0]

		url = 'https://api.openload.io/1/file/dlticket?file=%s' % id

		result = client.request(url)
		result = json.loads(result)

		cap = result['result']['captcha_url']

		if  not cap == None : cap = captcha.keyboard(cap)
		
		time.sleep(result['result']['wait_time'])

		url = 'https://api.openload.io/1/file/dl?file=%s&ticket=%s' % (id, result['result']['ticket'])

		if not cap == None : url += '&captcha_response=%s' % urllib.quote(cap)

		result = client.request(url)
		result = json.loads(result)
		
		urlVideo = result['result']['url'] + '?mime=true'

		return [urlVideo, urlLegenda]
		
def getVidzi(url):
		urlVideo   = '-'
		urlLegenda = '-'
		
		try:
				result = client.request(url, mobile=True, close=False)

				try:
						post = {}
						f = client.parseDOM(result, 'Form', attrs = {'method': 'POST'})[0]
						f = f.replace('"submit"', '"hidden"')
						k = client.parseDOM(f, 'input', ret='name', attrs = {'type': 'hidden'})
						for i in k: post.update({i: client.parseDOM(f, 'input', ret='value', attrs = {'name': i})[0]})
						post = urllib.urlencode(post)
				except:
						post = None

				for i in range(0, 10):
						try:
								request = client.request(url, post=post, mobile=True, close=False)
								request = request.replace('\n','')

								conteudo = re.compile('(eval.*?\)\)\))').findall(request)[-1]
								decode = jsunpack.unpack(conteudo)
								
								video = re.compile('sources *: *\[.+?\]').findall(decode)[-1]
								video = re.compile('file *: *"(http.+?)"').findall(video)
								
								urlV = [i for i in video if '.m3u8' in i]
								
								if len(urlV) > 0 : urlVideo = urlV[0]
								
								try :
										legenda = re.compile('tracks *: *\[.+?\]').findall(decode)[-1]
										legenda = re.compile('file *: *"(http.+?)"').findall(legenda)
										urlL = [i for i in legenda if '.srt' in i]
										
										if len(urlL) > 0 : urlLegenda = urlL[0]
										
								except :
										pass
								
								return [urlVideo, urlLegenda]
						except:
								time.sleep(1)
								
		except:
				return [urlVideo, urlLegenda]
				
def doPesquisa(url):
		teclado = xbmc.Keyboard('', 'CineCult - Pesquisa de Filmes')
		teclado.doModal()
		
		if (teclado.isConfirmed()): 
				texto = teclado.getText()
				pesquisa = urllib.quote(texto)
				url = base + '?s=%s' % str(pesquisa)
				getFilmes(url)

def openConfig():
		selfAddon.openSettings()
		setViewMenu()
		xbmcplugin.endOfDirectory(int(sys.argv[1]))

##############################################################################

def setViewMenu() :
		xbmcplugin.setContent(int(sys.argv[1]), 'movies')
		
		opcao = selfAddon.getSetting('menuVisu')
		
		if   opcao == '0': xbmc.executebuiltin("Container.SetViewMode(50)")
		elif opcao == '1': xbmc.executebuiltin("Container.SetViewMode(51)")
		elif opcao == '2': xbmc.executebuiltin("Container.SetViewMode(500)")
		
def setViewFilmes() :
		xbmcplugin.setContent(int(sys.argv[1]), 'movies')

		opcao = selfAddon.getSetting('filmesVisu')

		if   opcao == '0': xbmc.executebuiltin("Container.SetViewMode(50)")
		elif opcao == '1': xbmc.executebuiltin("Container.SetViewMode(51)")
		elif opcao == '2': xbmc.executebuiltin("Container.SetViewMode(500)")
		elif opcao == '3': xbmc.executebuiltin("Container.SetViewMode(501)")
		elif opcao == '4': xbmc.executebuiltin("Container.SetViewMode(508)")
		elif opcao == '5': xbmc.executebuiltin("Container.SetViewMode(504)")
		elif opcao == '6': xbmc.executebuiltin("Container.SetViewMode(503)")
		elif opcao == '7': xbmc.executebuiltin("Container.SetViewMode(515)")

def getImg(texto):
		texto = texto.lower()
		texto = texto.replace('ç','c').replace('ã','a').replace('õ','o')
		texto = texto.replace('â','a').replace('ê','e').replace('ô','o')
		texto = texto.replace('á','a').replace('é','e').replace('í','i').replace('Í','i').replace('ó','o').replace('ú','u').replace('ü','u')
		texto = texto.replace('Á','a')
		texto = texto.replace('&','').replace(' ', '-').replace('.', '-').replace(',', '-').replace('--','-')
		texto = texto + '.png'
		return texto
		
def openURL(url):
		req = urllib2.Request(url)
		
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		
		response = urllib2.urlopen(req)
		link     = response.read()
		
		response.close()
		
		return link
		
def addDir(name, url, mode, iconimage, pasta=True, total=1, plot=''):
		u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
		
		ok = True
		
		liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
		
		liz.setProperty('fanart_image', fanart)
		liz.setInfo(type = "Video", infoLabels = {"title": name, "plot": plot})
		
		ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=pasta, totalItems=total)

		return ok
		
##############################################################################
              
def get_params():
		param=[]
		paramstring=sys.argv[2]

		if len(paramstring)>=2:
				params=sys.argv[2]
				cleanedparams=params.replace('?','')
				
				if (params[len(params)-1]=='/'):
						params=params[0:len(params)-2]
						
				pairsofparams=cleanedparams.split('&')
				param={}
				
				for i in range(len(pairsofparams)):
						splitparams={}
						splitparams=pairsofparams[i].split('=')
						
						if (len(splitparams))==2:
								param[splitparams[0]]=splitparams[1]
		return param
				
params    = get_params()
url       = None
name      = None
mode      = None
iconimage = None

try    : url = urllib.unquote_plus(params["url"])
except : pass

try    : name = urllib.unquote_plus(params["name"])
except : pass

try    : iconimage=urllib.unquote_plus(params["iconimage"])
except : pass

try    : mode = int(params["mode"])
except : pass

#print "Mode: "+str(mode)
#print "URL: "+str(url)
#print "Name: "+str(name)
#print "Iconimage: "+str(iconimage)

##############################################################################

if   mode == None : menuPrincipal()
elif mode == 10   : getFilmes(url)
elif mode == 20   : getMenus(url,name)
elif mode == 30   : doPesquisa(url)
elif mode == 100  : doPlay(url, name)
elif mode == 999  : openConfig()
	
xbmcplugin.endOfDirectory(int(sys.argv[1]))