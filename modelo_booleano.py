# Programa que le um arquivo e retorna outro arquivo com os indices de cada aquivo lido

# bibliotecas 
from itertools import count
import os
import ssl 
import sys
import nltk
from nltk.corpus import mac_morpho
from pickle import load
from pickle import dump

# Variaveis do ssl, não sei ainda porque colocar
_create_unverified_https_context = ssl._create_unverified_context
ssl._create_default_https_context = _create_unverified_https_context


# variaveis mestre
stopwords = nltk.corpus.stopwords.words("portuguese")
stemmer = nltk.stem.RSLPStemmer()
lista_simbolos = ['.', ',', '!', '?', '...', '-', '\n', '\t', ' ']
lista_etiquetas = ['PREP', 'ART', 'KC', 'KS']
variaveis_consulta = ['!', '&', '|']

# funções

# Função que recebe o nome do arquivo e retorna uma lista com os dados tratados, ja sem símbolos e stopwords
def ler_arquivos(nome_arqv):
	lista_dados = []
	cop_lista = []
	

	arquivo_lido = open(nome_arqv, 'r', encoding='utf-8')
	lista_dados = arquivo_lido.read()
	lista_dados = lista_dados.lower()

	for simbolo in lista_simbolos:
		lista_dados = lista_dados.replace(simbolo,' ')

	arquivo_lido.close()

	lista_dados = lista_dados.split()
	cop_lista = lista_dados.copy()
	cop_lista = ' '.join([data for data in lista_dados if data not in stopwords])
	cop_lista = cop_lista.split()

	return cop_lista


# função que cria um arquivo binario para salvar tagger do etiquetador, para leitura mais rapida
# PS: executar o programa excluindo o .bin leva a uma execuçao bem mais demorada
def criar_tagger_bin():
	sentencas_etiquetadas = mac_morpho.tagged_sents()
	etiquetador_unigram = nltk.tag.UnigramTagger( sentencas_etiquetadas )
	output = open('etiqueta_tagger.bin', 'wb')
	dump(etiquetador_unigram, output, -1)
	output.close()


# funçao que le um arquivo binario de tag do unigram e retorna as tags para ser utilizada no etiquetador
def ler_tagger_bin():
	inpu = open('etiqueta_tagger.bin', 'rb')
	tagger = load(inpu)
	inpu.close()
	return tagger

# Função que trata os caracteres da lista
def trata_nome_arqv(lista):
	separador = ""
	lista = separador.join(lista)
	lista = lista.split()
	return lista

# Função para extrair o radical de um palavra
def extrair_radical(palavra):
	sem_rad = ''.join(stemmer.stem(palavra))
	return sem_rad


# pega o nome do arquivo com a lista de arquivos passado pela linha de comando e ja abre ele para leitura	
arquivo_base = open(sys.argv[1],'r')

# cria uma lista para receber os nomes dos arquivos que serão usados no indice
lista_arquivos = []
for linha in arquivo_base:
	lista_arquivos += linha

arquivo_base.close()

# pega o nome do arquivo com a consulta a ser pesquisada
arquivo_consulta = open(sys.argv[2],'r')

# cria uma variavel para receber a consulta que sera pesquisada
texto_consulta = arquivo_consulta.read().strip()
arquivo_consulta.close()


# lista que recebe o nome dos aquivos tratado para a utilização na abertura dos mesmos
lista_arquivos = trata_nome_arqv(lista_arquivos)

# dicionario que tem como relaçao o indice do arquivo e uma lista com os dados do arquivo respectivamente {indice_arquivo:[dados arquivo]}
dados_arqvs = {}
txt_arqvs = []

# contador para o indice do dicionario
num_arqv = 0

# for que para cada nome de arquivo ele executa a func ler_arquivos(nome do aquivo), e tem como saída o dicionario com os indices e dados de todos os arquivos da base 
for nome in lista_arquivos:
	txt_arqvs += ler_arquivos(nome)
	dados_arqvs[num_arqv] = ler_arquivos(nome)
	num_arqv+=1 

#if que faz a verificaçao se o arquivo binario ja existe, se sim ele le o arquivo, se nao ele cria o arquivo e le ele
if os.path.isfile('etiqueta_tagger.bin') == True:
	tagger = ler_tagger_bin()
else:
	criar_tagger_bin()
	tagger = ler_tagger_bin()

# for que trata os radicais das palavras
for n in range(len(dados_arqvs)):
	dados_etiquetados = tagger.tag(dados_arqvs[n])	
	dados_arqvs[n] = [stemmer.stem(dados_etiquetados[i][0]) for i in range(len(dados_etiquetados)) if dados_etiquetados[i][1] not in lista_etiquetas]
    
# gera o indice invertido em um dicionario
indice_invertido = {}
conjunto_termos_doc = set({})
cont = 1
for data in dados_arqvs.values():
	for item in data:
		conjunto_termos_doc.add(item)
		if item in indice_invertido:
			indice_invertido[item][cont] = data.count(item)
		else:
			indice_invertido[item] = {cont:data.count(item)}
	cont+=1


# separa cada item da consulta
lista_consultas = {}
resposta_consulta = set({})
quase_resposta = set({})
conjunto_not = set({})
conjunto_compara_and_1 = set({})
conjunto_compara_and_2 = set({})
conjunto_and = set({})
conjunto_or = set({})
num_consulta = 1

conjunto_documentos = {*range(1, len(lista_arquivos)+1)}

# for para separar cada consulta pelo operador OR
for consult in texto_consulta.replace(' ', '').replace('|',' ').split():
    lista_consultas[num_consulta] = consult
    num_consulta += 1



termo_consulta = []
for i in lista_consultas.values():
	if '!' in i and '&' not in i:
		termo_consulta = extrair_radical(i.replace('!',''))
		for num_doc in indice_invertido[termo_consulta].keys():
			for num_doc_conj in conjunto_documentos:
				if num_doc != num_doc_conj:
					conjunto_not.add(num_doc_conj)

	elif '&' in i and '!' not in i:
		for item in i.split('&'):
			for num_doc in indice_invertido[extrair_radical(item)].keys():
				if num_doc not in conjunto_compara_and_1:
					conjunto_compara_and_1.add(num_doc)
				else:
					conjunto_compara_and_2.add(num_doc)
				
		conjunto_and = conjunto_compara_and_1.intersection(conjunto_compara_and_2)

	elif '!' in i and '&' in i:
		for item in i.split('&'):
			if '!' in item:
				termo_consulta = extrair_radical(item.replace('!',''))
				for num_doc in indice_invertido[termo_consulta].keys():
					for num_doc_conj in conjunto_documentos:
						if num_doc != num_doc_conj:
							conjunto_not.add(num_doc_conj)
			else:
				for num_doc in indice_invertido[extrair_radical(item)].keys():
					conjunto_compara_and_1.add(num_doc)
		
		resposta_consulta = conjunto_not.intersection(conjunto_compara_and_1)

	elif '!' not in i and '&' not in i:
		termo_consulta = extrair_radical(i)
		for num_doc in indice_invertido[termo_consulta].keys():
			conjunto_or.add(num_doc)

if conjunto_and and conjunto_not:	
	quase_resposta = conjunto_and.intersection(conjunto_not)
elif conjunto_not and not conjunto_and:
	quase_resposta = conjunto_not
elif conjunto_and and not conjunto_not:
	quase_resposta = conjunto_and

resposta_consulta = quase_resposta.union(conjunto_or)

# criação do arquivo .txt do indice invertido
arquivo_indice = open('indice.txt', 'w')

for item in indice_invertido:
	arquivo_indice.write(item+str(indice_invertido[item]).replace(' ', '').replace('}', '').replace(',', ' ').replace(':', ',').replace('{', ': '))
	arquivo_indice.write('\n')


arquivo_indice.close()


#criação do arquivo .txt da resposta da consulta
arquivo_resposta = open('resposta.txt', 'w')

arquivo_resposta.write(str(len(resposta_consulta)))
arquivo_resposta.write('\n')

for item in resposta_consulta:
	arquivo_resposta.write(lista_arquivos[item-1])
	arquivo_resposta.write('\n')

arquivo_resposta.close()

