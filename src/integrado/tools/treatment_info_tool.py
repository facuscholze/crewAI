from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os

class TreatmentInfoInput(BaseModel):
    """Input schema for treatment information tool."""
    treatment_name: str = Field(..., description="Name of the treatment to get information about")
    info_type: str = Field(default="all", description="Type of information: price, effects, duration, or all")

class TreatmentInfoTool(BaseTool):
    name: str = "Treatment Information Tool"
    description: str = (
        "Get detailed information about Houston Aesthetics treatments including prices, "
        "effects, duration, and procedures. Use this when clients ask about specific treatments."
    )
    args_schema: Type[BaseModel] = TreatmentInfoInput

    def _run(self, treatment_name: str, info_type: str = "all") -> str:
        """Get treatment information for Houston Aesthetics"""
        
        # Base de datos de tratamientos
        treatments = {
            "botox": {
                "price": "$45,000 - $65,000 pesos (dependiendo de unidades)",
                "duration": "3-6 meses",
                "effects": "Hinchazón leve (1-3 días), moretones menores (3-7 días), sensibilidad temporal",
                "description": "Tratamiento anti-edad para reducir líneas de expresión",
                "zones": "Frente, entrecejo, patas de gallo, cuello"
            },
            "rellenos faciales": {
                "price": "$35,000 - $85,000 pesos",
                "duration": "6-12 meses", 
                "effects": "Hinchazón temporal, sensibilidad leve, moretones menores",
                "description": "Relleno de ácido hialurónico para restaurar volumen facial",
                "zones": "Labios, mejillas, surcos nasogenianos"
            },
            "tratamientos para cuello": {
                "price": "$25,000 - $40,000 pesos",
                "duration": "4-8 sesiones",
                "effects": "Enrojecimiento leve, sensibilidad temporal",
                "description": "Tratamiento combinado para rejuvenecimiento del cuello",
                "includes": "Radiofrecuencia, mesoterapia, masajes terapéuticos"
            },
            "tratamientos para rodillas": {
                "price": "$30,000 - $50,000 pesos",
                "duration": "6-10 sesiones",
                "effects": "Hinchazón mínima, moretones menores",
                "description": "Tratamiento para mejorar la apariencia de las rodillas",
                "includes": "Mesoterapia, radiofrecuencia, masajes"
            },
            "masajes terapéuticos": {
                "price": "$15,000 - $25,000 pesos",
                "duration": "60-90 minutos por sesión",
                "effects": "Ninguno, completamente seguro y relajante",
                "description": "Masajes profesionales para relajación y bienestar",
                "benefits": "Reduce estrés, mejora circulación, alivia tensiones"
            },
            "acupuntura": {
                "price": "$12,000 - $20,000 pesos",
                "duration": "45-60 minutos por sesión",
                "effects": "Muy raros, sensación de relajación profunda",
                "description": "Terapia tradicional china para equilibrio energético",
                "benefits": "Reduce dolor, mejora bienestar general, relajación"
            }
        }
        
        # Buscar tratamiento (case insensitive)
        treatment_key = None
        for key in treatments.keys():
            if treatment_name.lower() in key or key in treatment_name.lower():
                treatment_key = key
                break
        
        if not treatment_key:
            return f"Lo siento, no tengo información específica sobre '{treatment_name}'. Los tratamientos disponibles son: Botox, Rellenos faciales, Tratamientos para cuello, Tratamientos para rodillas, Masajes terapéuticos, y Acupuntura."
        
        treatment_info = treatments[treatment_key]
        
        # Formatear respuesta según el tipo de información solicitado
        if info_type.lower() == "price":
            return f"💰 Precio de {treatment_key.title()}: {treatment_info['price']}"
        elif info_type.lower() == "effects":
            return f"⚠️ Efectos secundarios de {treatment_key.title()}: {treatment_info['effects']}"
        elif info_type.lower() == "duration":
            return f"⏱️ Duración de {treatment_key.title()}: {treatment_info['duration']}"
        else:
            # Información completa
            response = f"📋 Información sobre {treatment_key.title()}:\n"
            response += f"💰 Precio: {treatment_info['price']}\n"
            response += f"⏱️ Duración: {treatment_info['duration']}\n"
            response += f"⚠️ Efectos secundarios: {treatment_info['effects']}\n"
            response += f"📝 Descripción: {treatment_info['description']}\n"
            
            if 'zones' in treatment_info:
                response += f"📍 Zonas tratadas: {treatment_info['zones']}\n"
            if 'includes' in treatment_info:
                response += f"🔧 Incluye: {treatment_info['includes']}\n"
            if 'benefits' in treatment_info:
                response += f"✨ Beneficios: {treatment_info['benefits']}\n"
            
            response += "\n💡 ¿Te gustaría agendar una consulta para más información?"
            
            return response




