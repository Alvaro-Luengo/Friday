package com.alvaro.friday.model

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val sender: String, // "USER" o "FRIDAY"
    val text: String,
    val timestamp: String = java.text.SimpleDateFormat("HH:mm", java.util.Locale.getDefault()).format(java.util.Date()),
    val isAction: Boolean = false,
    val actionType: String? = null,
    val actionDetail: String? = null
)

data class DailyWeather(
    val date: String,
    val dayName: String,
    val code: Int,
    val description: String,
    val tempMax: Int,
    val tempMin: Int,
    val rainProb: Int,
    val rainSum: Double
)

data class CurrentWeather(
    val temperature: Int,
    val apparentTemp: Int,
    val code: Int,
    val description: String,
    val windSpeed: Int,
    val humidity: Int,
    val rain: Double
)

data class WeatherReport(
    val city: String,
    val current: CurrentWeather,
    val forecast: List<DailyWeather>
)

data class PcStatus(
    val cpuPercent: Double = 0.0,
    val ramPercent: Double = 0.0,
    val ramUsedGb: Double = 0.0,
    val ramTotalGb: Double = 0.0,
    val diskPercent: Double = 0.0,
    val diskFreeGb: Double = 0.0,
    val batteryPercent: Int? = null,
    val isPlugged: Boolean = true,
    val isOnline: Boolean = false
)

data class AgyHistoryItem(
    val timestamp: String,
    val prompt: String,
    val status: String,
    val tools: List<String>,
    val response: String,
    val durationSeconds: Double = 0.0
)

data class ApprovalRequest(
    val reqId: String,
    val description: String,
    val prompt: String,
    val message: String
)
