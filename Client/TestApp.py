import ProjectSettings
from socket import SocketIO
from turtle import width
import requests
import CSECommon
import tkinter as tk
import CSEMapModel
import CSEScraper
import CSEMapView
import sys

def main():
    map_model = CSEMapModel.CSEMapModel()
    map_model.CreateFromScrape(CSEScraper.CurrentScrape)