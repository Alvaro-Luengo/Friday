package com.alvaro.friday

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.alvaro.friday.assistant.AssistantAction
import com.alvaro.friday.assistant.AssistantEngine
import com.alvaro.friday.model.*
import com.alvaro.friday.network.FridayApiClient
import com.alvaro.friday.theme.*
import kotlinx.coroutines.launch
import java.util.*

class MainActivity : ComponentActivity(), TextToSpeech.OnInitListener {

    private var speechRecognizer: SpeechRecognizer? = null
    private var tts: TextToSpeech? = null
    private var ttsReady = false

    // Estado reactivo compartido
    private val isListening = mutableStateOf(false)
    private val recognizedSpeech = mutableStateOf("")
    private val chatMessages = mutableStateListOf<ChatMessage>()
    private val agyTerminalOutput = mutableStateOf("")
    private val isAgyRunning = mutableStateOf(false)
    private val pendingApproval = mutableStateOf<ApprovalRequest?>(null)
    private val weatherData = mutableStateOf<WeatherReport?>(null)
    private val pcStatus = mutableStateOf<PcStatus?>(null)
    private val pcOnline = mutableStateOf(false)
    private val pcLatency = mutableStateOf<Long?>(null)
    private val agyHistoryList = mutableStateListOf<AgyHistoryItem>()

    // Configuración persistida en SharedPreferences
    private val serverUrlState = mutableStateOf("https://unburst-stacee-reforgeable.ngrok-free.dev")
    private val pinState = mutableStateOf("1234")
    private val momPhoneState = mutableStateOf("+34657188367")

    private val requestPermissionsLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val audioGranted = permissions[Manifest.permission.RECORD_AUDIO] == true
        if (audioGranted) {
            initSpeechRecognizer()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Cargar preferencias guardadas
        val prefs = getSharedPreferences("friday_prefs", Context.MODE_PRIVATE)
        serverUrlState.value = prefs.getString("server_url", "https://unburst-stacee-reforgeable.ngrok-free.dev") ?: "https://unburst-stacee-reforgeable.ngrok-free.dev"
        pinState.value = prefs.getString("pin", "1234") ?: "1234"
        momPhoneState.value = prefs.getString("mom_phone", "+34657188367") ?: "+34657188367"

        // Inicializar sintetizador de voz (TTS)
        tts = TextToSpeech(this, this)

        // Comprobar y pedir permisos
        checkAndRequestPermissions()

        // Mensaje inicial de bienvenida
        chatMessages.add(
            ChatMessage(
                sender = "FRIDAY",
                text = "Sistemas operativos, Álvaro. Asistente personal y puente con Antigravity en línea."
            )
        )

        // Comprobar estado inicial del PC en segundo plano
        refreshPcStatus()

        // Interfaz de usuario Compose
        setContent {
            FridayTheme {
                FridayAppContent(
                    isListening = isListening.value,
                    chatMessages = chatMessages,
                    agyTerminalOutput = agyTerminalOutput.value,
                    isAgyRunning = isAgyRunning.value,
                    pendingApproval = pendingApproval.value,
                    weatherData = weatherData.value,
                    pcStatus = pcStatus.value,
                    pcOnline = pcOnline.value,
                    pcLatency = pcLatency.value,
                    agyHistoryList = agyHistoryList,
                    serverUrl = serverUrlState.value,
                    pin = pinState.value,
                    momPhone = momPhoneState.value,
                    onStartVoice = { startListening() },
                    onStopVoice = { stopListening() },
                    onSendMessage = { text -> handleUserInput(text) },
                    onExecuteAgy = { prompt, skipPerms, continueSess ->
                        executeAgyPrompt(prompt, skipPerms, continueSess)
                    },
                    onResolveApproval = { reqId, approved ->
                        resolveApproval(reqId, approved)
                    },
                    onRefreshWeather = { loadWeather() },
                    onRefreshStatus = { refreshPcStatus() },
                    onRefreshHistory = { loadHistory() },
                    onSaveSettings = { url, pin, mom ->
                        saveSettings(url, pin, mom)
                    }
                )
            }
        }
    }

    private fun checkAndRequestPermissions() {
        val permissions = mutableListOf(Manifest.permission.RECORD_AUDIO)
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CALL_PHONE) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.CALL_PHONE)
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.READ_CONTACTS)
        }
        requestPermissionsLauncher.launch(permissions.toTypedArray())
    }

    private fun initSpeechRecognizer() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) return

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
        speechRecognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                isListening.value = true
                vibrate(40)
            }

            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}

            override fun onEndOfSpeech() {
                isListening.value = false
            }

            override fun onError(error: Int) {
                isListening.value = false
            }

            override fun onResults(results: Bundle?) {
                isListening.value = false
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    val query = matches[0]
                    recognizedSpeech.value = query
                    handleUserInput(query)
                }
            }

            override fun onPartialResults(partialResults: Bundle?) {
                val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    recognizedSpeech.value = matches[0]
                }
            }

            override fun onEvent(eventType: Int, params: Bundle?) {}
        })
    }

    private fun startListening() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            checkAndRequestPermissions()
            return
        }

        if (speechRecognizer == null) {
            initSpeechRecognizer()
        }

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "es-ES")
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "es-ES")
            putExtra(RecognizerIntent.EXTRA_ONLY_RETURN_LANGUAGE_PREFERENCE, "es-ES")
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }
        speechRecognizer?.startListening(intent)
        isListening.value = true
    }

    private fun stopListening() {
        speechRecognizer?.stopListening()
        isListening.value = false
    }

    private fun handleUserInput(query: String) {
        val clean = query.trim()
        if (clean.isEmpty()) return

        // Añadir mensaje del usuario
        chatMessages.add(ChatMessage(sender = "USER", text = clean))

        // Procesar acción inteligente
        when (val action = AssistantEngine.processQuery(this, clean, momPhoneState.value)) {
            is AssistantAction.OpenIntent -> {
                chatMessages.add(ChatMessage(sender = "FRIDAY", text = action.spokenResponse))
                speak(action.spokenResponse)
                try {
                    startActivity(action.intent)
                } catch (e: Exception) {
                    Toast.makeText(this, "No se pudo abrir la aplicación requerida: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
            is AssistantAction.SpeakOnly -> {
                chatMessages.add(ChatMessage(sender = "FRIDAY", text = action.message))
                speak(action.message)
            }
            is AssistantAction.FetchWeather -> {
                chatMessages.add(ChatMessage(sender = "FRIDAY", text = action.spokenPrompt))
                speak(action.spokenPrompt)
                loadWeather { spokenSummary ->
                    if (spokenSummary != null) {
                        chatMessages.add(ChatMessage(sender = "FRIDAY", text = spokenSummary))
                        speak(spokenSummary)
                    }
                }
            }
            is AssistantAction.FetchPcStatus -> {
                chatMessages.add(ChatMessage(sender = "FRIDAY", text = action.spokenPrompt))
                speak(action.spokenPrompt)
                refreshPcStatus { statusText ->
                    chatMessages.add(ChatMessage(sender = "FRIDAY", text = statusText))
                    speak(statusText)
                }
            }
            is AssistantAction.AskAgy -> {
                val promptMsg = "Enviando solicitud a Antigravity: '${action.task}'"
                chatMessages.add(ChatMessage(sender = "FRIDAY", text = promptMsg))
                speak("Consultando a Antigravity.")
                executeAgyPrompt(action.task, skipPermissions = true, continueSession = false)
            }
            is AssistantAction.SendPcGeneral -> {
                FridayApiClient.sendPcCommand(serverUrlState.value, pinState.value, clean) { resp, err ->
                    val text = resp ?: "No se pudo conectar con el PC: $err"
                    chatMessages.add(ChatMessage(sender = "FRIDAY", text = text))
                    speak(text)
                }
            }
        }
    }

    private fun executeAgyPrompt(prompt: String, skipPermissions: Boolean, continueSession: Boolean) {
        isAgyRunning.value = true
        agyTerminalOutput.value = "> agy -p \"$prompt\" ${if (skipPermissions) "--dangerously-skip-permissions" else ""} ${if (continueSession) "-c" else ""}\n[Iniciando ejecución...]\n"

        FridayApiClient.streamAgy(
            baseUrl = serverUrlState.value,
            pin = pinState.value,
            prompt = prompt,
            skipPermissions = skipPermissions,
            continueSession = continueSession,
            onChunk = { delta ->
                agyTerminalOutput.value += delta
            },
            onToolCall = { tool, summary ->
                agyTerminalOutput.value += "\n⚡ [HERRAMIENTA: $tool] $summary\n"
            },
            onApprovalRequired = { req ->
                pendingApproval.value = req
                vibrate(100)
            },
            onStatus = { status ->
                agyTerminalOutput.value += "ℹ️ $status\n"
            },
            onError = { err ->
                agyTerminalOutput.value += "\n❌ ERROR: $err\n"
                isAgyRunning.value = false
            },
            onFinished = { finalResponse ->
                agyTerminalOutput.value += "\n✅ FINALIZADO.\n"
                isAgyRunning.value = false
                loadHistory()
            }
        )
    }

    private fun resolveApproval(reqId: String, approved: Boolean) {
        FridayApiClient.approveAction(serverUrlState.value, pinState.value, reqId, approved) { success, _ ->
            pendingApproval.value = null
            agyTerminalOutput.value += if (approved) {
                "\n🟢 Autorización confirmada por el usuario móvil. Continuando ejecución...\n"
            } else {
                "\n🔴 Acción cancelada por el usuario móvil.\n"
            }
        }
    }

    private fun refreshPcStatus(onComplete: ((String) -> Unit)? = null) {
        FridayApiClient.checkStatus(serverUrlState.value, pinState.value) { success, status, latency, err ->
            pcOnline.value = success
            pcLatency.value = latency
            pcStatus.value = status

            if (onComplete != null) {
                if (success && status != null) {
                    val batStr = if (status.batteryPercent != null) ", batería al ${status.batteryPercent}%" else ""
                    val msg = "Ordenador en línea. CPU al ${status.cpuPercent.toInt()}%, memoria RAM al ${status.ramPercent.toInt()}% (${status.ramUsedGb} GB de ${status.ramTotalGb} GB) y almacenamiento al ${status.diskPercent.toInt()}%$batStr."
                    onComplete(msg)
                } else {
                    onComplete("No se pudo obtener el estado del PC: ${err ?: "Sin respuesta"}")
                }
            }
        }
    }

    private fun loadWeather(onComplete: ((String?) -> Unit)? = null) {
        FridayApiClient.fetchWeather(serverUrlState.value, pinState.value) { report, _ ->
            weatherData.value = report
            if (report != null) {
                val cur = report.current
                val summary = "En ${report.city} tenemos ${cur.temperature} grados con ${cur.description}, sensación de ${cur.apparentTemp} grados y viento a ${cur.windSpeed} km/h."
                onComplete?.invoke(summary)
            } else {
                onComplete?.invoke("No se pudo obtener el pronóstico del tiempo.")
            }
        }
    }

    private fun loadHistory() {
        FridayApiClient.fetchHistory(serverUrlState.value, pinState.value) { list, _ ->
            if (list != null) {
                agyHistoryList.clear()
                agyHistoryList.addAll(list)
            }
        }
    }

    private fun saveSettings(url: String, pin: String, mom: String) {
        serverUrlState.value = url.trim()
        pinState.value = pin.trim()
        momPhoneState.value = mom.trim()

        val prefs = getSharedPreferences("friday_prefs", Context.MODE_PRIVATE)
        prefs.edit()
            .putString("server_url", serverUrlState.value)
            .putString("pin", pinState.value)
            .putString("mom_phone", momPhoneState.value)
            .apply()

        Toast.makeText(this, "Ajustes de Friday guardados correctamente", Toast.LENGTH_SHORT).show()
        refreshPcStatus()
    }

    private fun speak(text: String) {
        if (!ttsReady || tts == null) return
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "FRIDAY_MSG")
    }

    private fun vibrate(durationMs: Long) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vm = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                vm?.defaultVibrator?.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                val v = getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                @Suppress("DEPRECATION")
                v?.vibrate(durationMs)
            }
        } catch (_: Exception) {}
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            val result = tts?.setLanguage(Locale("es", "ES"))
            if (result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED) {
                ttsReady = true
                tts?.setPitch(1.05f)
                tts?.setSpeechRate(1.15f)
            }
        }
    }

    override fun onDestroy() {
        speechRecognizer?.destroy()
        tts?.stop()
        tts?.shutdown()
        super.onDestroy()
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FridayAppContent(
    isListening: Boolean,
    chatMessages: List<ChatMessage>,
    agyTerminalOutput: String,
    isAgyRunning: Boolean,
    pendingApproval: ApprovalRequest?,
    weatherData: WeatherReport?,
    pcStatus: PcStatus?,
    pcOnline: Boolean,
    pcLatency: Long?,
    agyHistoryList: List<AgyHistoryItem>,
    serverUrl: String,
    pin: String,
    momPhone: String,
    onStartVoice: () -> Unit,
    onStopVoice: () -> Unit,
    onSendMessage: (String) -> Unit,
    onExecuteAgy: (String, Boolean, Boolean) -> Unit,
    onResolveApproval: (String, Boolean) -> Unit,
    onRefreshWeather: () -> Unit,
    onRefreshStatus: () -> Unit,
    onRefreshHistory: () -> Unit,
    onSaveSettings: (String, String, String) -> Unit
) {
    var selectedTab by remember { mutableIntStateOf(0) }

    Scaffold(
        containerColor = CyberBg,
        topBar = {
            FridayHeader(
                pcOnline = pcOnline,
                latency = pcLatency,
                onHeaderClick = onRefreshStatus
            )
        },
        bottomBar = {
            FridayBottomNav(
                selectedTab = selectedTab,
                onTabSelect = { tabIndex ->
                    selectedTab = tabIndex
                    if (tabIndex == 1) onRefreshHistory()
                    if (tabIndex == 2) onRefreshHistory()
                }
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            when (selectedTab) {
                0 -> AssistantScreen(
                    isListening = isListening,
                    chatMessages = chatMessages,
                    weatherData = weatherData,
                    pcStatus = pcStatus,
                    onStartVoice = onStartVoice,
                    onStopVoice = onStopVoice,
                    onSendMessage = onSendMessage,
                    onQuickAction = { query -> onSendMessage(query) },
                    onRefreshWeather = onRefreshWeather
                )
                1 -> AgyTerminalScreen(
                    terminalOutput = agyTerminalOutput,
                    isRunning = isAgyRunning,
                    pendingApproval = pendingApproval,
                    onExecute = onExecuteAgy,
                    onResolveApproval = onResolveApproval
                )
                2 -> HistoryScreen(
                    history = agyHistoryList,
                    onRefresh = onRefreshHistory
                )
                3 -> SettingsScreen(
                    currentUrl = serverUrl,
                    currentPin = pin,
                    currentMom = momPhone,
                    pcOnline = pcOnline,
                    latency = pcLatency,
                    pcStatus = pcStatus,
                    onSave = onSaveSettings,
                    onTestConnection = onRefreshStatus
                )
            }
        }
    }
}

@Composable
fun FridayHeader(
    pcOnline: Boolean,
    latency: Long?,
    onHeaderClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .background(CyberCard, shape = RoundedCornerShape(14.dp))
            .border(1.dp, CyberCardBorder, RoundedCornerShape(14.dp))
            .clickable { onHeaderClick() }
            .padding(horizontal = 14.dp, vertical = 10.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            // Arc Reactor mini logo
            Box(
                modifier = Modifier
                    .size(24.dp)
                    .clip(CircleShape)
                    .border(2.dp, NeonCyan, CircleShape)
                    .background(Color.Black),
                contentAlignment = Alignment.Center
            ) {
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .clip(CircleShape)
                        .background(NeonCyan)
                )
            }
            Spacer(modifier = Modifier.width(10.dp))
            Text(
                text = "FRIDAY V2.0",
                fontSize = 17.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 2.sp,
                color = Color.White
            )
        }

        // Estado del PC
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(if (pcOnline) CyberSuccess else CyberDanger)
            )
            Spacer(modifier = Modifier.width(6.dp))
            Text(
                text = if (pcOnline) "PC EN LÍNEA ${latency?.let { "(${it}ms)" } ?: ""}" else "PC DESCONECTADO",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                color = if (pcOnline) CyberSuccess else CyberDanger
            )
        }
    }
}

@Composable
fun FridayBottomNav(
    selectedTab: Int,
    onTabSelect: (Int) -> Unit
) {
    NavigationBar(
        containerColor = CyberCard,
        contentColor = NeonCyan,
        modifier = Modifier.border(BorderStroke(1.dp, CyberCardBorder))
    ) {
        val items = listOf("🎙️ ASISTENTE", "⚡ AGY CLI", "📋 HISTORIAL", "⚙️ AJUSTES")
        items.forEachIndexed { index, label ->
            NavigationBarItem(
                selected = selectedTab == index,
                onClick = { onTabSelect(index) },
                icon = {
                    Text(
                        text = label.split(" ")[0],
                        fontSize = 18.sp
                    )
                },
                label = {
                    Text(
                        text = label.split(" ")[1],
                        fontSize = 11.sp,
                        fontWeight = if (selectedTab == index) FontWeight.Bold else FontWeight.Normal,
                        color = if (selectedTab == index) NeonCyan else CyberTextDim
                    )
                },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = NeonCyan,
                    selectedTextColor = NeonCyan,
                    indicatorColor = NeonCyanDim
                )
            )
        }
    }
}

@Composable
fun AssistantScreen(
    isListening: Boolean,
    chatMessages: List<ChatMessage>,
    weatherData: WeatherReport?,
    pcStatus: PcStatus?,
    onStartVoice: () -> Unit,
    onStopVoice: () -> Unit,
    onSendMessage: (String) -> Unit,
    onQuickAction: (String) -> Unit,
    onRefreshWeather: () -> Unit
) {
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()
    var textInput by remember { mutableStateOf("") }

    LaunchedEffect(chatMessages.size) {
        if (chatMessages.isNotEmpty()) {
            listState.animateScrollToItem(chatMessages.size - 1)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Reactor Arc grande pulsante (Centro de activación por voz)
        Spacer(modifier = Modifier.height(10.dp))
        ArcReactorVoiceButton(
            isListening = isListening,
            onClick = {
                if (isListening) onStopVoice() else onStartVoice()
            }
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Fila de acciones rápidas (WhatsApp, Llamar, Spotify, Tiempo, Estado PC)
        LazyRow(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            val chips = listOf(
                "💬 WhatsApp Mamá" to "mensaje a mamá",
                "📞 Llamar a Mamá" to "llama a mamá",
                "🎵 Spotify Rock" to "modo poder",
                "🌤️ El Tiempo" to "qué tiempo hace",
                "💻 Estado del PC" to "cómo está el pc",
                "📅 ¿Qué hora es?" to "qué hora es"
            )
            items(chips) { (label, command) ->
                Button(
                    onClick = { onQuickAction(command) },
                    colors = ButtonDefaults.buttonColors(containerColor = CyberCard),
                    border = BorderStroke(1.dp, CyberCardBorder),
                    shape = RoundedCornerShape(20.dp),
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                ) {
                    Text(text = label, fontSize = 12.sp, color = CyberText)
                }
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Widget Meteorológico si está disponible
        if (weatherData != null) {
            WeatherWidget(weatherData)
            Spacer(modifier = Modifier.height(8.dp))
        }

        // Historial de mensajes y respuestas del asistente
        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(chatMessages) { msg ->
                ChatBubble(msg)
            }
        }

        // Barra inferior de texto y botón enviar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            TextField(
                value = textInput,
                onValueChange = { textInput = it },
                modifier = Modifier
                    .weight(1f)
                    .background(CyberCard, RoundedCornerShape(12.dp))
                    .border(1.dp, CyberCardBorder, RoundedCornerShape(12.dp)),
                placeholder = { Text("Escribe una petición a Friday...", color = CyberTextDim, fontSize = 13.sp) },
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = CyberCard,
                    unfocusedContainerColor = CyberCard,
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent
                ),
                maxLines = 2
            )

            Spacer(modifier = Modifier.width(8.dp))

            Button(
                onClick = {
                    if (textInput.isNotBlank()) {
                        onSendMessage(textInput)
                        textInput = ""
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = NeonCyan),
                shape = RoundedCornerShape(12.dp),
                contentPadding = PaddingValues(12.dp)
            ) {
                Text("➤", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 16.sp)
            }
        }
    }
}

@Composable
fun ArcReactorVoiceButton(
    isListening: Boolean,
    onClick: () -> Unit
) {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val scale by infiniteTransition.animateFloat(
        initialValue = if (isListening) 1f else 0.95f,
        targetValue = if (isListening) 1.15f else 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(if (isListening) 500 else 1800, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(
            modifier = Modifier
                .size(90.dp)
                .scale(scale)
                .clip(CircleShape)
                .border(3.dp, if (isListening) CyberSuccess else NeonCyan, CircleShape)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            if (isListening) CyberSuccess.copy(alpha = 0.4f) else NeonCyan.copy(alpha = 0.25f),
                            Color.Transparent
                        )
                    )
                )
                .clickable { onClick() },
            contentAlignment = Alignment.Center
        ) {
            Box(
                modifier = Modifier
                    .size(46.dp)
                    .clip(CircleShape)
                    .border(2.dp, if (isListening) CyberSuccess else CyberBlue, CircleShape)
                    .background(if (isListening) CyberSuccess else NeonCyan),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = if (isListening) "🔊" else "🎤",
                    fontSize = 22.sp
                )
            }
        }

        Spacer(modifier = Modifier.height(6.dp))
        Text(
            text = if (isListening) "FRIDAY ESCUCHANDO..." else "TOCA PARA HABLAR",
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            letterSpacing = 1.sp,
            color = if (isListening) CyberSuccess else NeonCyan
        )
    }
}

@Composable
fun ChatBubble(msg: ChatMessage) {
    val isUser = msg.sender == "USER"
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Box(
            modifier = Modifier
                .widthIn(max = 300.dp)
                .background(
                    if (isUser) CyberBlue.copy(alpha = 0.25f) else CyberCard,
                    shape = RoundedCornerShape(12.dp)
                )
                .border(
                    1.dp,
                    if (isUser) CyberBlue else CyberCardBorder,
                    RoundedCornerShape(12.dp)
                )
                .padding(12.dp)
        ) {
            Column {
                Text(
                    text = if (isUser) "ÁLVARO" else "FRIDAY",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    color = if (isUser) CyberBlue else NeonCyan
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = msg.text,
                    fontSize = 14.sp,
                    color = CyberText
                )
            }
        }
    }
}

@Composable
fun WeatherWidget(report: WeatherReport) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = CyberCard),
        border = BorderStroke(1.dp, CyberCardBorder),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "🌤️ TIEMPO EN ${report.city.uppercase()} (${report.current.temperature}°C)",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = NeonCyan
                )
                Text(
                    text = report.current.description,
                    fontSize = 11.sp,
                    color = CyberTextDim
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(report.forecast) { day ->
                    Column(
                        modifier = Modifier
                            .background(CyberBg, RoundedCornerShape(8.dp))
                            .border(1.dp, CyberCardBorder, RoundedCornerShape(8.dp))
                            .padding(horizontal = 8.dp, vertical = 6.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(text = day.dayName, fontSize = 11.sp, fontWeight = FontWeight.Bold, color = CyberText)
                        Text(text = "${day.tempMax}° / ${day.tempMin}°", fontSize = 10.sp, color = CyberBlue)
                        if (day.rainProb > 0) {
                            Text(text = "🌧️ ${day.rainProb}%", fontSize = 9.sp, color = NeonCyan)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun AgyTerminalScreen(
    terminalOutput: String,
    isRunning: Boolean,
    pendingApproval: ApprovalRequest?,
    onExecute: (String, Boolean, Boolean) -> Unit,
    onResolveApproval: (String, Boolean) -> Unit
) {
    var promptInput by remember { mutableStateOf("") }
    var skipPermissions by remember { mutableStateOf(true) }
    var continueSession by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            text = "⚡ CONSOLA EN VIVO DE ANTIGRAVITY (AGY)",
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            color = NeonCyan,
            letterSpacing = 1.sp
        )
        Text(
            text = "Ejecución remota directa en el PC con streaming y supervisor de seguridad.",
            fontSize = 11.sp,
            color = CyberTextDim
        )

        Spacer(modifier = Modifier.height(10.dp))

        // Alerta de confirmación de seguridad si se requiere
        if (pendingApproval != null) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = CyberDanger.copy(alpha = 0.2f)),
                border = BorderStroke(2.dp, CyberDanger),
                shape = RoundedCornerShape(12.dp)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(
                        text = "⚠️ CONFIRMACIÓN DE SEGURIDAD REQUERIDA",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        color = CyberDanger
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = pendingApproval.message,
                        fontSize = 12.sp,
                        color = Color.White
                    )
                    Spacer(modifier = Modifier.height(10.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.End
                    ) {
                        Button(
                            onClick = { onResolveApproval(pendingApproval.reqId, false) },
                            colors = ButtonDefaults.buttonColors(containerColor = Color.DarkGray)
                        ) {
                            Text("Rechazar", color = Color.White)
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        Button(
                            onClick = { onResolveApproval(pendingApproval.reqId, true) },
                            colors = ButtonDefaults.buttonColors(containerColor = CyberDanger)
                        ) {
                            Text("Autorizar", color = Color.White, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
            Spacer(modifier = Modifier.height(10.dp))
        }

        // Opciones de ejecución AGY
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(
                    checked = skipPermissions,
                    onCheckedChange = { skipPermissions = it },
                    colors = CheckboxDefaults.colors(checkedColor = NeonCyan)
                )
                Text("--skip-permissions", fontSize = 11.sp, fontFamily = FontFamily.Monospace, color = CyberText)
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(
                    checked = continueSession,
                    onCheckedChange = { continueSession = it },
                    colors = CheckboxDefaults.colors(checkedColor = NeonCyan)
                )
                Text("-c (continuar)", fontSize = 11.sp, fontFamily = FontFamily.Monospace, color = CyberText)
            }
        }

        // Terminal de logs
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .background(Color.Black, RoundedCornerShape(8.dp))
                .border(1.dp, CyberCardBorder, RoundedCornerShape(8.dp))
                .padding(10.dp)
                .verticalScroll(rememberScrollState())
        ) {
            Text(
                text = if (terminalOutput.isEmpty()) "Listo para recibir instrucciones para AGY...\nEjemplo: 'Crea un script en Python que analice el uso de memoria'" else terminalOutput,
                fontFamily = FontFamily.Monospace,
                fontSize = 11.sp,
                color = if (isRunning) NeonCyan else CyberText
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Input de comando AGY
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextField(
                value = promptInput,
                onValueChange = { promptInput = it },
                modifier = Modifier
                    .weight(1f)
                    .background(CyberCard, RoundedCornerShape(10.dp))
                    .border(1.dp, CyberCardBorder, RoundedCornerShape(10.dp)),
                placeholder = { Text("Petición a AGY...", color = CyberTextDim, fontSize = 12.sp) },
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = CyberCard,
                    unfocusedContainerColor = CyberCard,
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent
                )
            )
            Spacer(modifier = Modifier.width(8.dp))
            Button(
                onClick = {
                    if (promptInput.isNotBlank() && !isRunning) {
                        onExecute(promptInput, skipPermissions, continueSession)
                        promptInput = ""
                    }
                },
                enabled = !isRunning,
                colors = ButtonDefaults.buttonColors(containerColor = NeonCyan),
                shape = RoundedCornerShape(10.dp)
            ) {
                Text(if (isRunning) "..." else "Ejecutar", color = Color.Black, fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
fun HistoryScreen(
    history: List<AgyHistoryItem>,
    onRefresh: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "📋 HISTORIAL DE OPERACIONES AGY",
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = NeonCyan
            )
            Button(
                onClick = onRefresh,
                colors = ButtonDefaults.buttonColors(containerColor = CyberCard),
                border = BorderStroke(1.dp, CyberCardBorder),
                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
            ) {
                Text("Actualizar", fontSize = 11.sp, color = CyberText)
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        if (history.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Text("No hay registros recientes de Antigravity.", color = CyberTextDim, fontSize = 13.sp)
            }
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(history) { item ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = CyberCard),
                        border = BorderStroke(1.dp, CyberCardBorder),
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = item.status,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = if (item.status == "COMPLETED" || item.status == "SUCCESS") CyberSuccess else CyberDanger
                                )
                                Text(
                                    text = item.timestamp.take(19).replace("T", " "),
                                    fontSize = 10.sp,
                                    color = CyberTextDim
                                )
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "💬 \"${item.prompt}\"",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                            if (item.tools.isNotEmpty()) {
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    text = "Herramientas usadas: ${item.tools.joinToString(", ")}",
                                    fontSize = 11.sp,
                                    color = CyberBlue
                                )
                            }
                            if (item.response.isNotEmpty()) {
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    text = item.response.take(150) + if (item.response.length > 150) "..." else "",
                                    fontSize = 11.sp,
                                    color = CyberTextDim
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun SettingsScreen(
    currentUrl: String,
    currentPin: String,
    currentMom: String,
    pcOnline: Boolean,
    latency: Long?,
    pcStatus: PcStatus?,
    onSave: (String, String, String) -> Unit,
    onTestConnection: () -> Unit
) {
    var urlInput by remember { mutableStateOf(currentUrl) }
    var pinInput by remember { mutableStateOf(currentPin) }
    var momInput by remember { mutableStateOf(currentMom) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "⚙️ AJUSTES DE CONEXIÓN CON EL PC",
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            color = NeonCyan
        )
        Text(
            text = "Enlace del servidor Friday en tu ordenador (Ngrok / Cloudflare / Wi-Fi local).",
            fontSize = 11.sp,
            color = CyberTextDim
        )

        Spacer(modifier = Modifier.height(14.dp))

        Text("Dirección del Servidor (URL):", fontSize = 12.sp, color = CyberText)
        TextField(
            value = urlInput,
            onValueChange = { urlInput = it },
            modifier = Modifier
                .fillMaxWidth()
                .background(CyberCard, RoundedCornerShape(8.dp))
                .border(1.dp, CyberCardBorder, RoundedCornerShape(8.dp)),
            colors = TextFieldDefaults.colors(
                focusedContainerColor = CyberCard,
                unfocusedContainerColor = CyberCard,
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White
            )
        )

        Spacer(modifier = Modifier.height(10.dp))

        Text("PIN de Seguridad:", fontSize = 12.sp, color = CyberText)
        TextField(
            value = pinInput,
            onValueChange = { pinInput = it },
            modifier = Modifier
                .fillMaxWidth()
                .background(CyberCard, RoundedCornerShape(8.dp))
                .border(1.dp, CyberCardBorder, RoundedCornerShape(8.dp)),
            colors = TextFieldDefaults.colors(
                focusedContainerColor = CyberCard,
                unfocusedContainerColor = CyberCard,
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White
            )
        )

        Spacer(modifier = Modifier.height(10.dp))

        Text("Teléfono de Mamá (WhatsApp y Llamadas):", fontSize = 12.sp, color = CyberText)
        TextField(
            value = momInput,
            onValueChange = { momInput = it },
            modifier = Modifier
                .fillMaxWidth()
                .background(CyberCard, RoundedCornerShape(8.dp))
                .border(1.dp, CyberCardBorder, RoundedCornerShape(8.dp)),
            colors = TextFieldDefaults.colors(
                focusedContainerColor = CyberCard,
                unfocusedContainerColor = CyberCard,
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White
            )
        )

        Spacer(modifier = Modifier.height(16.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Button(
                onClick = onTestConnection,
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(containerColor = CyberCard),
                border = BorderStroke(1.dp, CyberCardBorder)
            ) {
                Text("Probar Enlace", color = CyberText)
            }
            Button(
                onClick = { onSave(urlInput, pinInput, momInput) },
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(containerColor = NeonCyan)
            ) {
                Text("Guardar", color = Color.Black, fontWeight = FontWeight.Bold)
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Diagnóstico actual del PC
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = CyberCard),
            border = BorderStroke(1.dp, CyberCardBorder),
            shape = RoundedCornerShape(10.dp)
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = "ESTADO DEL EQUIPO",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = NeonCyan
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = if (pcOnline) "🟢 Conexión Activa (${latency ?: 0}ms)" else "🔴 Sin Conexión",
                    color = if (pcOnline) CyberSuccess else CyberDanger,
                    fontSize = 12.sp
                )
                if (pcStatus != null) {
                    Spacer(modifier = Modifier.height(6.dp))
                    Text("• CPU: ${pcStatus.cpuPercent}%", fontSize = 11.sp, color = CyberText)
                    Text("• Memoria RAM: ${pcStatus.ramPercent}% (${pcStatus.ramUsedGb} GB / ${pcStatus.ramTotalGb} GB)", fontSize = 11.sp, color = CyberText)
                    Text("• Disco Principal: ${pcStatus.diskPercent}% (${pcStatus.diskFreeGb} GB libres)", fontSize = 11.sp, color = CyberText)
                    if (pcStatus.batteryPercent != null) {
                        Text("• Batería: ${pcStatus.batteryPercent}% (${if (pcStatus.isPlugged) "Cargando" else "Batería"})", fontSize = 11.sp, color = CyberText)
                    }
                }
            }
        }
    }
}
