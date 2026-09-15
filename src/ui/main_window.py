#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hauptfenster - Geldausgabe mit Schnellwahltasten (OHNE Bestätigung)
"""

import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QMessageBox, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from src.hardware.motor_control import MotorController


class MainWindow(QMainWindow):
    """Hauptfenster mit Schnellwahlbuttons - OHNE Bestätigung"""
    
    # Schnellwahl Beträge
    QUICK_AMOUNTS = [5, 10, 20, 50, 100, 200, 500]
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.motor = None
        self.selected_amount = 0
        
        self.setup_ui()
        self.init_motor()
    
    def setup_ui(self):
        """Erstellt GUI mit Schnellwahltasten"""
        self.setWindowTitle(f"💰 GELDAUTOMAT - {self.config.atm_name}")
        self.setGeometry(100, 100, 800, 700)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ===== TITEL =====
        title = QLabel("💵 GELDAUTOMAT 💵")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2ecc71; padding: 20px;")
        main_layout.addWidget(title)
        
        # ===== BETRAG ANZEIGE =====
        self.amount_display = QLabel("0 €")
        amount_display_font = QFont()
        amount_display_font.setPointSize(48)
        amount_display_font.setBold(True)
        self.amount_display.setFont(amount_display_font)
        self.amount_display.setAlignment(Qt.AlignCenter)
        self.amount_display.setStyleSheet("color: #27ae60; background-color: white; padding: 30px; border-radius: 10px; border: 3px solid #2ecc71;")
        main_layout.addWidget(self.amount_display)
        
        # ===== SCHNELLWAHL BUTTONS (GRID) =====
        quick_label = QLabel("⚡ WÄHLEN SIE EINEN BETRAG:")
        quick_label_font = QFont()
        quick_label_font.setPointSize(14)
        quick_label_font.setBold(True)
        quick_label.setFont(quick_label_font)
        main_layout.addWidget(quick_label)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # Erstelle Schnellwahl Buttons in 2 Reihen
        for idx, amount in enumerate(self.QUICK_AMOUNTS):
            btn = self.create_quick_button(amount)
            row = idx // 4  # 4 Buttons pro Reihe
            col = idx % 4
            grid_layout.addWidget(btn, row, col)
        
        main_layout.addLayout(grid_layout)
        
        # ===== MANUELLE EINGABE =====
        manual_label = QLabel("✏️ ODER BETRAG MANUELL EINGEBEN:")
        manual_label_font = QFont()
        manual_label_font.setPointSize(12)
        manual_label_font.setBold(True)
        manual_label.setFont(manual_label_font)
        main_layout.addWidget(manual_label)
        
        manual_layout = QHBoxLayout()
        self.amount_spin = QSpinBox()
        self.amount_spin.setMinimum(self.config.min_amount)
        self.amount_spin.setMaximum(self.config.max_amount)
        self.amount_spin.setValue(20)
        self.amount_spin.setSingleStep(5)
        self.amount_spin.setStyleSheet("font-size: 18px; padding: 10px; min-width: 100px;")
        self.amount_spin.valueChanged.connect(self.update_amount_display)
        manual_layout.addWidget(QLabel("Betrag (€):"))
        manual_layout.addWidget(self.amount_spin)
        manual_layout.addStretch()
        main_layout.addLayout(manual_layout)
        
        # ===== HAUPTBUTTON - DIREKTE AUSZAHLUNG =====
        withdraw_btn = QPushButton("💰 GELD SOFORT AUSGEBEN")
        withdraw_btn.setMinimumHeight(70)
        withdraw_btn.setStyleSheet(
            "background-color: #e74c3c; color: white; font-size: 22px; font-weight: bold; "
            "border-radius: 10px; border: none; padding: 10px;"
        )
        withdraw_btn.clicked.connect(self.withdraw_immediate)
        main_layout.addWidget(withdraw_btn)
        
        # ===== KONTROLLBUTTONS =====
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        test_btn = QPushButton("🔧 Motor Test")
        test_btn.setMinimumHeight(50)
        test_btn.setStyleSheet("background-color: #3498db; color: white; font-size: 14px; border-radius: 5px;")
        test_btn.clicked.connect(self.test_motor)
        control_layout.addWidget(test_btn)
        
        clear_btn = QPushButton("🔄 Zurücksetzen")
        clear_btn.setMinimumHeight(50)
        clear_btn.setStyleSheet("background-color: #95a5a6; color: white; font-size: 14px; border-radius: 5px;")
        clear_btn.clicked.connect(self.reset)
        control_layout.addWidget(clear_btn)
        
        main_layout.addLayout(control_layout)
        
        # ===== STATUS =====
        self.status_label = QLabel("✅ Bereit - Wählen Sie einen Betrag")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 16px; padding: 15px; background-color: white; border-radius: 5px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        main_layout.addStretch()
    
    def create_quick_button(self, amount):
        """Erstellt einen Schnellwahl Button"""
        btn = QPushButton(f"💵 {amount}€")
        btn.setMinimumHeight(60)
        btn.setStyleSheet(
            "background-color: #3498db; color: white; font-size: 18px; font-weight: bold; "
            "border-radius: 8px; border: 2px solid #2980b9; padding: 10px;"
        )
        btn.clicked.connect(lambda: self.select_and_dispense(amount))
        return btn
    
    def select_and_dispense(self, amount):
        """Wählt Betrag und gibt sofort Geld aus - OHNE Bestätigung"""
        self.amount_spin.setValue(amount)
        self.update_amount_display()
        # Geld sofort ausgeben
        self.withdraw_immediate()
    
    def update_amount_display(self):
        """Aktualisiert Betrag-Anzeige"""
        amount = self.amount_spin.value()
        self.amount_display.setText(f"{amount} €")
        self.selected_amount = amount
    
    def init_motor(self):
        """Initialisiert Motor"""
        try:
            self.motor = MotorController(self.config.motor_port)
            if self.motor.connect():
                self.update_status("✅ Motor verbunden - Bereit", "#2ecc71")
            else:
                self.update_status("⚠️ Motor-Fehler", "#e74c3c")
        except Exception as e:
            self.logger.error(f"Motor Init: {str(e)}")
            self.update_status(f"❌ Fehler: {str(e)}", "#e74c3c")
    
    def withdraw_immediate(self):
        """Gibt Geld SOFORT aus - OHNE Bestätigung"""
        amount = self.amount_spin.value()
        
        if amount < self.config.min_amount or amount > self.config.max_amount:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Betrag muss zwischen {self.config.min_amount}€ und {self.config.max_amount}€ liegen"
            )
            return
        
        if not self.motor or not self.motor.is_connected:
            QMessageBox.critical(self, "Fehler", "🔌 Motor nicht verbunden")
            self.update_status("❌ Motor-Fehler", "#e74c3c")
            return
        
        try:
            self.update_status(f"⏳ Zahle {amount}€ aus...", "#f39c12")
            self.logger.info(f"Geldausgabe: {amount}€ - SOFORT")
            
            if self.motor.dispense_money(amount):
                self.update_status(f"✅ {amount}€ ausgegeben!", "#2ecc71")
                
                # Kurze Erfolgs-Nachricht
                QMessageBox.information(
                    self,
                    "✅ Erfolg",
                    f"💵 {amount}€ wurden ausgegeben!\\n\\n👉 Bitte Geld entnehmen."
                )
                
                # Nach 3 Sekunden zurücksetzen
                QTimer.singleShot(3000, self.reset)
            else:
                self.update_status("❌ Auszahlung fehlgeschlagen", "#e74c3c")
                QMessageBox.critical(
                    self,
                    "Fehler",
                    "❌ Motor konnte kein Geld ausgeben\\n\\nBitte versuchen Sie es später erneut."
                )
                
        except Exception as e:
            self.logger.error(f"Fehler: {str(e)}")
            self.update_status("❌ Fehler", "#e74c3c")
            QMessageBox.critical(self, "Fehler", f"❌ Auszahlung fehlgeschlagen:\\n{str(e)}")
    
    def test_motor(self):
        """Testet Motor mit 10€"""
        if not self.motor or not self.motor.is_connected:
            QMessageBox.warning(self, "Fehler", "🔌 Motor nicht verbunden")
            return
        
        reply = QMessageBox.question(
            self,
            "🔧 Motortest",
            "Testet Motor mit Ausgabe von 10€\\n\\n✅ = Test starten\\n❌ = Abbrechen",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.update_status("⏳ Führe Motortest durch...", "#f39c12")
            if self.motor.dispense_money(10):
                self.update_status("✅ Motor funktioniert!", "#2ecc71")
                QMessageBox.information(self, "✅ Test erfolgreich", "✅ Motor funktioniert einwandfrei!")
            else:
                self.update_status("⚠️ Motor reagiert nicht", "#e74c3c")
                QMessageBox.warning(self, "⚠️ Test fehlgeschlagen", "⚠️ Motor reagiert nicht auf Befehle")
    
    def reset(self):
        """Setzt Eingabe zurück"""
        self.amount_spin.setValue(20)
        self.update_amount_display()
        self.update_status("✅ Bereit - Wählen Sie einen Betrag", "#27ae60")
    
    def update_status(self, message, color):
        """Aktualisiert Status"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px; padding: 15px; background-color: white; border-radius: 5px;")
        self.logger.info(f"Status: {message}")
    
    def closeEvent(self, event):
        """Cleanup beim Schließen"""
        if self.motor:
            self.motor.disconnect()
        event.accept()
