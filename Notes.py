# """
# les boucles
# """
# # boucle while
# a = 2

# while a < 10:
#     print("Le nomùbre vaut", a)
#     a += 1
    
# # boucle for, exemple
# voiture = ["BMW", "MERCEDESS", "TOYOTA", "KPANDJI"]
# for voiture in voiture:
#     print("j'aime la", voiture)
    
    
         
# # exemple boucle while        
# certification = input("Avez-vous une certification? :")

# while certification != "OUI" and certification != "NON":
#     print("Réponse invalide, répondez par OUI ou NON")
#     certification = input("Avez-vous une certification? :")

# if certification == "OUI":
#     print("bravo")
# else:
#     print("dommage")
    
    
    
# """
# les fonctions 
# """
# # exemple 1
# def dire (nom_personne, message_personne, age_personne):
#     print("{} ({}ans) : {}".format(nom_personne, age_personne, message_personne))
    
# dire(nom_personne= "PYO", age_personne= 21, message_personne= "ciouciou")

# #Exemple 2
# def show_inventory(*list_items):
#     for item in list_items:
#         print(item)
        
# show_inventory("epée", "arc", "potion de mana", "cape")

# #Exemple 3
# def calculer_somme(nombre1, nombre2):
#     return nombre1 + nombre2

# print(calculer_somme(2,3))

# #Exemple 4
# def le_plus_grand(nombrex, nombrey):
#     if nombrex > nombrey:
#         return nombrex
#     elif nombrey > nombrex:
#         return nombrey
#     else:
#         return "égalité"

# print(le_plus_grand(3, 3))


# """
# créer et importer module : exemple module player

# """
# import Includes.Player as Player

# Additionner = Player.addition(2,4)
# print(Additionner)


# from Includes.Player import soustraction

# print(soustraction(8,9))

#"as player" simplifie le chemin d'accès
     

"""
Les listes
"""

# liste[x] = Affiche élément d'indice x
# liste[-x]   =  Affiche xème élément en partant de la fin

# liste[:]    = Affiche tout les élméments
# liste[:x]   = Affiche les x premiers éléments
# liste[x:]   = Affiche les x derniers éléments 

# liste[A:B]  = Affiche de l'élément d'indice A à l'élément d'indice B (exclus)

# remplacer des éléments dans une liste:
    # inventaire = ["arc", "epee", "bouclier", "potion", "flèche", "tunique"]
    # print(inventaire)

    # inventaire[2]= "étuie"
    # inventaire [-1] = "mana"
    # print(inventaire) 

    # inventaire[1:4] = ["cape"]*3
    # print(inventaire)
    
# faire un parcours
         # for valeur in list:
            # print(valeur)
    
# faire de la recherche dans une liste avec "if x in list"


# Methodes

    # list.append         = ajouter un élément
    # list.insert(1, "x") = ajoute l'élément x à l'indice 1
    # list.remove("x")    = supprime l'élément x de la liste
    # del liste[1]        = supprime l'élément en indice 1
    # list.index("x")     = donne l'indice de l'élément "x"
    # list.sort           = trie, range par ordre
    # list.reverse        = inverse les valeurs, trie décroissant
    # list.count("x")     = compte le nombre de fois qu'il y a x dans la liste
    # list.clear()        = efface tout les elements de la liste; ou:
                                                                        # inventaire = []
                                                                        # print(inventaire) 
    # list1.extend.list2    = fusionne la liste 1 et 2 ou:
                                                            # list1 += list2
                                                            

"""
Les dictionnaires
"""
# dico[clé] = valeur   = ajoute la clé et sa valeur au dico, ou modifie si l'élément existe
# dico[clé]              = accès à une valeur du dico via sa clé
# dico.pop(clé)          = supprimme la valeur via sa clé ou:
                                                            #  del dico[clé]
# faire de la recherche dans un dico avec "if 'clé' in dico"

# faire un parcours 
    # afficher les clés:
                # for key in dico:
                #     print(key)

    # afficher les valeurs:     
                # for valeurs in dico.values:
                #     print(valeurs)
    # afficher clé et valeur:
                # for k,v in dico.items():
                #     print(k,v)

"""
on sait jamais
"""
# Training

"""
présentation du producteur
"""
Nom_producteur = input("Veuillez entrer votre nom: ")

superficie = input("Sur quelle superficie cultivez-vous? (en hectares): ")

""""
recensement des cultures
"""
cultures = {}
compteur = 1

while True:
    nom = input("Entrez le nom de votre culture (ou ecrivez 'fin' pour fermer): " )
    if nom.lower() == "fin":
        break

    cle = f"Spéculation{compteur:02d}"
    cultures[cle] = nom
    compteur += 1
    
print("\nCultures enregistrées :")
for cle , nom in cultures.items():
    print(f"{cle} : {nom}")

print(cultures)


"""
calcul du revenu
"""

production = int(input("Quelle est votre production?: "))
prix = 438

def revenu(production, prix):
    return production * prix

revenu_total = revenu(production, prix)
print("votre revenu est", revenu_total)

Speculations = ",".join(cultures.values())
print("Bonjour monsieur {} , votre plantation de {} hectars de {} vous a rapporté {} FCFA".format(Nom_producteur, superficie, Speculations, revenu_total ))


"""
Certification du producteur
"""
bonus = 15
def revenu_final(revenu, bonus):
    return revenu + bonus

certification = input("Avez-vous une certification ? (OUI/NON): ")

while certification.upper() not in ["OUI", "NON"]:
    print("Veuillez répondre par OUI OU NON. ")
    certification = input("Avez-vous une certification? (OUI/NON) : ")
    
if certification.upper() == "OUI":
    revenu_bonus = revenu_final(revenu_total, bonus)
    print("Etant donné que vous êtes certifiés, vous obtenez un bonus de 15 FCFA sur votre revenu")
    print("Votre revenu final est de: ", revenu_bonus, "FCFA")
else:
    print("Veuillez vous faire certifier afin de bénéficier de bonus sur revenus")

print("Informations enregistrées avec succès, merci pour votre collaboratrion")



                #####conception appli intégrée

import streamlit as st
import os
import shutil

# Dossier contenant les bases de données
DB_FOLDER = "data"
MODEL_DB = os.path.join(DB_FOLDER, "modèle_base.db")

# Création d'une coopérative (par duplication du modèle vide)
def creer_nouvelle_cooperative(nom_coop):
    nom_fichier = f"coop_{nom_coop.lower().replace(' ', '_')}.db"
    chemin_fichier = os.path.join(DB_FOLDER, nom_fichier)

    if os.path.exists(chemin_fichier):
        st.warning("Cette coopérative existe déjà.")
    else:
        shutil.copyfile(MODEL_DB, chemin_fichier)
        st.success(f"Coopérative '{nom_coop}' créée avec succès !")
        st.session_state["db_path"] = chemin_fichier
        st.session_state["nom_coop"] = nom_coop
        st.rerun()

# Page d'accueil multi-coopératives
def accueil():
    st.title("Portail des Coopératives")

    st.subheader("1. Sélectionner une coopérative existante")
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    fichiers_db = [f for f in os.listdir(DB_FOLDER) if f.endswith(".db") and f != "modèle_base.db"]
    noms_coops = [f.replace("coop_", "").replace(".db", "").replace("_", " ").title() for f in fichiers_db]

    if noms_coops:
        choix = st.selectbox("Choisissez une coopérative :", noms_coops)
        if st.button("Accéder à la coopérative"):
            index = noms_coops.index(choix)
            st.session_state["db_path"] = os.path.join(DB_FOLDER, fichiers_db[index])
            st.session_state["nom_coop"] = choix
            st.success(f"Connexion à la coopérative : {choix}")
            st.rerun()
    else:
        st.info("Aucune coopérative disponible. Créez-en une nouvelle.")

    st.divider()
    st.subheader("2. Créer une nouvelle coopérative")
    with st.expander("Nouvelle coopérative"):
        nouveau_nom = st.text_input("Nom de la coopérative")
        if st.button("Créer"):
            if nouveau_nom:
                creer_nouvelle_cooperative(nouveau_nom)
            else:
                st.error("Veuillez entrer un nom valide.")
