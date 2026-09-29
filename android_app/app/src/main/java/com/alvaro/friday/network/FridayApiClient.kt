package com.alvaro.friday.network

import android.os.Handler
import android.os.Looper
import com.alvaro.friday.model.*
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

object FridayApiClient {
    private val executor = Executors.newCachedThreadPool()
    private val mainHandler = Handler(Looper.getMainLooper())

    private fun postToMain(action: () -> Unit) {
        mainHandler.post(action)
    }

    private fun cleanUrl(baseUrl: String, endpoint: String): String {
        val base = baseUrl.trim().removeSuffix("/")
        val ep = endpoint.trim().removePrefix("/")
        return "$base/$ep"
    }

    fun checkStatus(
        baseUrl: String,
        pin: String,
        onResult: (Boolean, PcStatus?, Long, String?) -> Unit
    ) {
        executor.execute {
            val startTime = System.currentTimeMillis()
            var conn: HttpURLConnection? = null
            try {
                val fullUrl = cleanUrl(baseUrl, "/api/status")
                val url = URL(fullUrl)
                conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "GET"
                conn.connectTimeout = 6000
                conn.readTimeout = 6000
                conn.setRequestProperty("X-Jarvis-PIN", pin)
                conn.setRequestProperty("X-Friday-PIN", pin)

                val code = conn.responseCode
                val latency = System.currentTimeMillis() - startTime
                if (code == 200) {
                    val reader = BufferedReader(InputStreamReader(conn.inputStream, "UTF-8"))
                    val response = reader.readText()
                    reader.close()

                    val json = JSONObject(response)
                    val metrics = json.optJSONObject("metrics") ?: JSONObject()
                    val pcStatus = PcStatus(
                        cpuPercent = metrics.optDouble("cpu_percent", 0.0),
                        ramPercent = metrics.optDouble("ram_percent", 0.0),
                        ramUsedGb = metrics.optDouble("ram_used_gb", 0.0),
                        ramTotalGb = metrics.optDouble("ram_total_gb", 0.0),
                        diskPercent = metrics.optDouble("disk_percent", 0.0),
                        diskFreeGb = metrics.optDouble("disk_free_gb", 0.0),
                        batteryPercent = if (metrics.has("battery_percent") && !metrics.isNull("battery_percent")) metrics.getInt("battery_percent") else null,
                        isPlugged = metrics.optBoolean("power_plugged", true),
                        isOnline = true
                    )
                    postToMain { onResult(true, pcStatus, latency, null) }
                } else {
                    val err = "Error HTTP $code: ${conn.responseMessage}"
                    postToMain { onResult(false, null, latency, err) }
                }
            } catch (e: Exception) {
                val latency = System.currentTimeMillis() - startTime
                postToMain { onResult(false, null, latency, e.localizedMessage ?: "Fallo de conexión") }
            } finally {
                conn?.disconnect()
            }
        }
    }

    fun fetchWeather(
        baseUrl: String,
        pin: String,
        onResult: (WeatherReport?, String?) -> Unit
    ) {
        executor.execute {
            var conn: HttpURLConnection? = null
            try {
                val fullUrl = cleanUrl(baseUrl, "/api/weather")
                val url = URL(fullUrl)
                conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "GET"
                conn.connectTimeout = 8000
                conn.readTimeout = 8000
                conn.setRequestProperty("X-Jarvis-PIN", pin)
                conn.setRequestProperty("X-Friday-PIN", pin)

                if (conn.responseCode == 200) {
                    val reader = BufferedReader(InputStreamReader(conn.inputStream, "UTF-8"))
                    val response = reader.readText()
                    reader.close()

                    val json = JSONObject(response)
                    val city = json.optString("city", "Madrid")
                    val curObj = json.optJSONObject("current") ?: JSONObject()
                    val current = CurrentWeather(
                        temperature = curObj.optInt("temperature", 20),
                        apparentTemp = curObj.optInt("apparent_temperature", 20),
                        code = curObj.optInt("weather_code", 0),
                        description = curObj.optString("description", "Cielo variable"),
                        windSpeed = curObj.optInt("wind_speed", 0),
                        humidity = curObj.optInt("humidity", 50),
                        rain = curObj.optDouble("rain", 0.0)
                    )

                    val forecastList = mutableListOf<DailyWeather>()
                    val fArray = json.optJSONArray("forecast") ?: JSONArray()
                    for (i in 0 until fArray.length()) {
                        val item = fArray.getJSONObject(i)
                        forecastList.add(
                            DailyWeather(
                                date = item.optString("date", ""),
                                dayName = item.optString("day_name", ""),
                                code = item.optInt("code", 0),
                                description = item.optString("description", ""),
                                tempMax = item.optInt("temp_max", 0),
                                tempMin = item.optInt("temp_min", 0),
                                rainProb = item.optInt("rain_prob", 0),
                                rainSum = item.optDouble("rain_sum", 0.0)
                            )
                        )
                    }

                    val report = WeatherReport(city, current, forecastList)
                    postToMain { onResult(report, null) }
                } else {
                    postToMain { onResult(null, "Error HTTP ${conn.responseCode}") }
                }
            } catch (e: Exception) {
                postToMain { onResult(null, e.localizedMessage) }
            } finally {
                conn?.disconnect()
            }
        }
    }

    fun sendPcCommand(
        baseUrl: String,
        pin: String,
        command: String,
        onResult: (String?, String?) -> Unit
    ) {
        executor.execute {
            var conn: HttpURLConnection? = null
            try {
                val fullUrl = cleanUrl(baseUrl, "/api/command")
                val url = URL(fullUrl)
                conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.connectTimeout = 20000
                conn.readTimeout = 20000
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json")
                conn.setRequestProperty("X-Jarvis-PIN", pin)
                conn.setRequestProperty("X-Friday-PIN", pin)

                val body = JSONObject()
                body.put("command", command)
                body.put("speak_pc", false)

                val writer = OutputStreamWriter(conn.outputStream, "UTF-8")
                writer.write(body.toString())
                writer.flush()
                writer.close()

                if (conn.responseCode == 200) {
                    val reader = BufferedReader(InputStreamReader(conn.inputStream, "UTF-8"))
                    val response = reader.readText()
                    reader.close()
                    val json = JSONObject(response)
                    val resText = json.optString("response", "Comando procesado.")
                    postToMain { onResult(resText, null) }
                } else {
                    postToMain { onResult(null, "Error HTTP ${conn.responseCode}") }
                }
            } catch (e: Exception) {
                postToMain { onResult(null, e.localizedMessage) }
            } finally {
                conn?.disconnect()
            }
        }
    }

    fun approveAction(
        baseUrl: String,
        pin: String,
        approvalId: String,
        approved: Boolean,
        onResult: (Boolean, String?) -> Unit
    ) {
        executor.execute {
            var conn: HttpURLConnection? = null
            try {
                val fullUrl = cleanUrl(baseUrl, "/api/agy/approve")
                val url = URL(fullUrl)
                conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.connectTimeout = 10000
                conn.readTimeout = 10000
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json")
                conn.setRequestProperty("X-Jarvis-PIN", pin)
                conn.setRequestProperty("X-Friday-PIN", pin)

                val body = JSONObject()
                body.put("approval_id", approvalId)
                body.put("approved", approved)

                val writer = OutputStreamWriter(conn.outputStream, "UTF-8")
                writer.write(body.toString())
                writer.flush()
                writer.close()

                val code = conn.responseCode
                postToMain { onResult(code == 200, null) }
            } catch (e: Exception) {
                postToMain { onResult(false, e.localizedMessage) }
            } finally {
                conn?.disconnect()
            }
        }
    }

    fun fetchHistory(
        baseUrl: String,
        pin: String,
        onResult: (List<AgyHistoryItem>?, String?) -> Unit
    ) {
        executor.execute {
            var conn: HttpURLConnection? = null
            try {
                val fullUrl = cleanUrl(baseUrl, "/api/agy/history?limit=30")
                val url = URL(fullUrl)
                conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "GET"
                conn.connectTimeout = 8000
                conn.readTimeout = 8000
                conn.setRequestProperty("X-Jarvis-PIN", pin)
                conn.setRequestProperty("X-Friday-PIN", pin)

                if (conn.responseCode == 200) {
                    val reader = BufferedReader(InputStreamReader(conn.inputStream, "UTF-8"))
                    val response = reader.readText()
                    reader.close()

                    val json = JSONObject(response)
                    val array = json.optJSONArray("history") ?: JSONArray()
                    val list = mutableListOf<AgyHistoryItem>()
                    for (i in 0 until array.length()) {
                        val item = array.getJSONObject(i)
                        val toolsArray = item.optJSONArray("tools_called") ?: JSONArray()
                        val tools = mutableListOf<String>()
                        for (t in 0 until toolsArray.length()) {
                            val toolObj = toolsArray.optJSONObject(t)
                            if (toolObj != null) {
                                tools.add(toolObj.optString("name", "herramienta"))
                            } else {
                                tools.add(toolsArray.optString(t, "herramienta"))
                            }
                        }
                        list.add(
                            AgyHistoryItem(
                                timestamp = item.optString("timestamp", ""),
                                prompt = item.optString("prompt", ""),
                                status = item.optString("status", "COMPLETED"),
                                tools = tools,
                                response = item.optString("response", ""),
                                durationSeconds = item.optDouble("duration_seconds", 0.0)
                            )
                        )
                    }
                    postToMain { onResult(list, null) }
                } else {
                    postToMain { onResult(null, "Error HTTP ${conn.responseCode}") }
                }
            } catch (e: Exception) {
                postToMain { onResult(null, e.localizedMessage) }
            } finally {
                conn?.disconnect()
            }
        }
    }

    fun streamAgy(
        baseUrl: String,
        pin: String,
        prompt: String,
        skipPermissions: Boolean = true,
        continueSession: Boolean = false,
        onChunk: (String) -> Unit,
        onToolCall: (String, String) -> Unit,
        onApprovalRequired: (ApprovalRequest) -> Unit,
        onStatus: (String) -> Unit,
        onError: (String) -> Unit,
        onFinished: (String) -> Unit
    ) {
        executor.execute {
            var conn: HttpURLConnection? = null
            var fullResponseBuilder = StringBuilder()
            try {
                val fullUrl = cleanUrl(baseUrl, "/api/agy/stream")
                val url = URL(fullUrl)
                conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.connectTimeout = 15000
                conn.readTimeout = 180000 // 3 minutos para tareas complejas de AGY
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json")
                conn.setRequestProperty("Accept", "text/event-stream")
                conn.setRequestProperty("X-Jarvis-PIN", pin)
                conn.setRequestProperty("X-Friday-PIN", pin)

                val body = JSONObject()
                body.put("prompt", prompt)
                body.put("skip_permissions", skipPermissions)
                body.put("continue_session", continueSession)

                val writer = OutputStreamWriter(conn.outputStream, "UTF-8")
                writer.write(body.toString())
                writer.flush()
                writer.close()

                if (conn.responseCode == 200) {
                    val reader = BufferedReader(InputStreamReader(conn.inputStream, "UTF-8"))
                    var line: String?
                    while (reader.readLine().also { line = it } != null) {
                        val trimmed = line!!.trim()
                        if (trimmed.startsWith("data:")) {
                            val jsonStr = trimmed.removePrefix("data:").trim()
                            if (jsonStr.isEmpty()) continue
                            try {
                                val ev = JSONObject(jsonStr)
                                val type = ev.optString("type", "")

                                when (type) {
                                    "start" -> {
                                        postToMain { onStatus("Iniciando sesión con Antigravity...") }
                                    }
                                    "init" -> {
                                        val convId = ev.optString("conversation_id", "")
                                        postToMain { onStatus("Sesión AGY activa ($convId)") }
                                    }
                                    "text_delta" -> {
                                        val delta = ev.optString("delta", "")
                                        fullResponseBuilder.append(delta)
                                        postToMain { onChunk(delta) }
                                    }
                                    "tool_call" -> {
                                        val toolObj = ev.optJSONObject("tool") ?: JSONObject()
                                        val name = toolObj.optString("name", "herramienta")
                                        val summary = toolObj.optString("summary", "")
                                        postToMain { onToolCall(name, summary) }
                                    }
                                    "approval_required" -> {
                                        val req = ApprovalRequest(
                                            reqId = ev.optString("approval_id", ""),
                                            description = ev.optString("description", ""),
                                            prompt = ev.optString("prompt", ""),
                                            message = ev.optString("message", "")
                                        )
                                        postToMain { onApprovalRequired(req) }
                                    }
                                    "approval_rejected" -> {
                                        val msg = ev.optString("message", "Operación rechazada por seguridad.")
                                        postToMain { onError(msg) }
                                    }
                                    "result" -> {
                                        val res = ev.optString("response", "")
                                        if (res.isNotEmpty() && fullResponseBuilder.isEmpty()) {
                                            fullResponseBuilder.append(res)
                                        }
                                    }
                                    "error" -> {
                                        val err = ev.optString("message", "Error desconocido")
                                        postToMain { onError(err) }
                                    }
                                    "done" -> {
                                        val finalResp = ev.optString("final_response", fullResponseBuilder.toString())
                                        postToMain { onFinished(finalResp) }
                                        break
                                    }
                                }
                            } catch (e: Exception) {
                                // Salida no json
                            }
                        }
                    }
                    reader.close()
                } else {
                    val err = "Error HTTP ${conn.responseCode}: ${conn.responseMessage}"
                    postToMain { onError(err) }
                }
            } catch (e: Exception) {
                postToMain { onError(e.localizedMessage ?: "Error de red con el servidor") }
            } finally {
                conn?.disconnect()
            }
        }
    }
}
