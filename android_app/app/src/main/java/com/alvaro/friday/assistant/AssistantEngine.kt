package com.alvaro.friday.assistant

import android.app.SearchManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.MediaStore
import java.text.SimpleDateFormat
import java.util.*

sealed class AssistantAction {
    data class OpenIntent(val intent: Intent, val spokenResponse: String) : AssistantAction()
    data class SpeakOnly(val message: String) : AssistantAction()
    data class FetchWeather(val spokenPrompt: String = "Consultando el pronóstico del tiempo...") : AssistantAction()
    data class FetchPcStatus(val spokenPrompt: String = "Comprobando métricas del ordenador...") : AssistantAction()
    data class AskAgy(val task: String) : AssistantAction()
    data class SendPcGeneral(val query: String) : AssistantAction()
}

object AssistantEngine {

    private val DIAS = arrayOf("domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado")
    private val MESES = arrayOf("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")

    fun processQuery(context: Context, rawQuery: String, defaultMomPhone: String = "+34657188367"): AssistantAction {
        val query = rawQuery.trim().lowercase(Locale.ROOT)
        if (query.isEmpty()) {
            return AssistantAction.SpeakOnly("¿En qué puedo ayudarte, Álvaro?")
        }

        // 1. FECHA Y HORA
        if (query.contains("qué hora") || query.contains("que hora") || query.contains("la hora") || query.contains("tienes hora")) {
            val cal = Calendar.getInstance()
            val horaStr = SimpleDateFormat("HH:mm", Locale.getDefault()).format(cal.time)
            return AssistantAction.SpeakOnly("Son las $horaStr.")
        }
        if (query.contains("qué día") || query.contains("que dia") || query.contains("fecha") || query.contains("qué fecha")) {
            val cal = Calendar.getInstance()
            val diaSem = DIAS[cal.get(Calendar.DAY_OF_WEEK) - 1]
            val diaNum = cal.get(Calendar.DAY_OF_MONTH)
            val mes = MESES[cal.get(Calendar.MONTH)]
            val anio = cal.get(Calendar.YEAR)
            val horaStr = SimpleDateFormat("HH:mm", Locale.getDefault()).format(cal.time)
            return AssistantAction.SpeakOnly("Hoy es $diaSem, $diaNum de $mes de $anio, y son las $horaStr.")
        }

        // 2. WHATSAPP
        if (query.contains("whatsapp") || query.contains("guasap") || (query.contains("mensaje") && query.contains("mamá"))) {
            var msgText = ""
            var targetPhone = defaultMomPhone
            var targetName = "Mamá"

            if (query.contains("diciendo") || query.contains("que diga") || query.contains("dice")) {
                val parts = query.split(Regex("diciendo|que diga|dice"), 2)
                if (parts.size > 1) {
                    msgText = parts[1].trim()
                }
            } else if (query.contains("mensaje a mamá") || query.contains("mensaje a mama")) {
                msgText = "Hola mamá, ¿cómo estás?"
            }

            if (!query.contains("mamá") && !query.contains("mama")) {
                targetName = "contacto"
            }

            val encodedMsg = Uri.encode(msgText)
            val cleanPhone = targetPhone.replace("+", "").replace(" ", "").trim()
            val url = if (cleanPhone.isNotEmpty()) {
                "https://api.whatsapp.com/send?phone=$cleanPhone&text=$encodedMsg"
            } else {
                "https://api.whatsapp.com/send?text=$encodedMsg"
            }

            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
                setPackage("com.whatsapp")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            return AssistantAction.OpenIntent(intent, "Abriendo WhatsApp para $targetName.")
        }

        // 3. LLAMADAS TELEFÓNICAS
        if (query.startsWith("llama") || query.startsWith("llamar") || query.startsWith("marcar") || query.contains("haz una llamada")) {
            var number = defaultMomPhone
            var contactName = "Mamá"

            val clean = query.replace("llama a", "")
                .replace("llamar a", "")
                .replace("marcar al", "")
                .replace("marcar a", "")
                .replace("haz una llamada a", "")
                .trim()

            if (clean.contains("mamá") || clean.contains("mama")) {
                number = defaultMomPhone
                contactName = "Mamá"
            } else if (clean.replace(Regex("[^0-9]"), "").length >= 9) {
                number = clean.replace(Regex("[^0-9+]"), "")
                contactName = number
            } else if (clean.isNotEmpty()) {
                contactName = clean
            }

            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$number")).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            return AssistantAction.OpenIntent(intent, "Marcando llamada para $contactName.")
        }

        // 4. SPOTIFY / MÚSICA
        if (query.contains("spotify") || query.contains("pon ") || query.contains("reproduce") || query.contains("modo poder")) {
            var song = ""
            if (query.contains("modo poder") || query.contains("modo energia")) {
                song = "AC/DC Back in Black"
            } else {
                val prefixes = arrayOf(
                    "reproduce en spotify", "pon en spotify", "busca en spotify", "en spotify",
                    "reproduce la canción", "reproducir la canción", "pon la canción", "pon la música",
                    "reproduce", "reproducir", "toca", "pon", "play", "spotify"
                )
                var temp = query
                for (p in prefixes) {
                    temp = temp.replace(p, "")
                }
                song = temp.trim()
            }

            if (song.isEmpty()) {
                val launchIntent = context.packageManager.getLaunchIntentForPackage("com.spotify.music")
                if (launchIntent != null) {
                    launchIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK
                    return AssistantAction.OpenIntent(launchIntent, "Abriendo Spotify.")
                }
                val viewIntent = Intent(Intent.ACTION_VIEW, Uri.parse("spotify:")).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                return AssistantAction.OpenIntent(viewIntent, "Abriendo Spotify.")
            }

            val searchIntent = Intent(MediaStore.INTENT_ACTION_MEDIA_PLAY_FROM_SEARCH).apply {
                putExtra(MediaStore.EXTRA_MEDIA_FOCUS, "vnd.android.cursor.item/*")
                putExtra(SearchManager.QUERY, song)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                setPackage("com.spotify.music")
            }
            return AssistantAction.OpenIntent(searchIntent, "Reproduciendo $song en Spotify.")
        }

        // 5. TIEMPO METEOROLÓGICO (HOY Y SEMANA)
        if (query.contains("tiempo") || query.contains("clima") || query.contains("llover") || query.contains("temperatura") || query.contains("pronóstico")) {
            return AssistantAction.FetchWeather()
        }

        // 6. ESTADO DEL PC
        if (query.contains("cómo está el pc") || query.contains("como esta el pc") || query.contains("estado del pc") ||
            query.contains("estado del ordenador") || query.contains("recursos del pc") || query.contains("rendimiento del pc")) {
            return AssistantAction.FetchPcStatus()
        }

        // 7. UBICACIÓN Y MAPAS
        if (query.contains("dónde estoy") || query.contains("donde estoy") || query.contains("cómo ir") || query.contains("como ir") || query.contains("llévame a")) {
            var destination = ""
            val prefixes = arrayOf("cómo ir a", "como ir a", "llévame a", "llevame a", "ruta a")
            for (p in prefixes) {
                if (query.contains(p)) {
                    destination = query.substringAfter(p).trim()
                    break
                }
            }
            val mapUri = if (destination.isNotEmpty()) {
                Uri.parse("geo:0,0?q=${Uri.encode(destination)}")
            } else {
                Uri.parse("geo:0,0?q=mi+ubicacion")
            }
            val mapIntent = Intent(Intent.ACTION_VIEW, mapUri).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                setPackage("com.google.android.apps.maps")
            }
            val resp = if (destination.isNotEmpty()) "Calculando ruta a $destination en Google Maps." else "Mostrando tu ubicación en Google Maps."
            return AssistantAction.OpenIntent(mapIntent, resp)
        }

        // 8. BÚSQUEDA EN INTERNET / GOOGLE
        if (query.startsWith("busca en google") || query.startsWith("buscar en google") || query.startsWith("busca en internet") || query.startsWith("busca ")) {
            val q = query.replace("busca en google", "")
                .replace("buscar en google", "")
                .replace("busca en internet", "")
                .replace("buscar en internet", "")
                .replace("busca", "")
                .trim()
            val searchIntent = Intent(Intent.ACTION_WEB_SEARCH).apply {
                putExtra(SearchManager.QUERY, q)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            return AssistantAction.OpenIntent(searchIntent, "Buscando $q en Google.")
        }

        // 9. ANTIGRAVITY AGY
        if (query.contains("antigravity") || query.contains("agy") || query.contains("pregunta a agy") || query.contains("pregunta a antigravity")) {
            var task = query.replace("pregunta a agy", "")
                .replace("pregunta a antigravity", "")
                .replace("antigravity", "")
                .replace("agy", "")
                .trim()
            if (task.isEmpty()) task = "explica qué herramientas tienes activas"
            return AssistantAction.AskAgy(task)
        }

        // 10. COMANDO GENERAL AL SERVIDOR DE FRIDAY
        return AssistantAction.SendPcGeneral(rawQuery)
    }
}
