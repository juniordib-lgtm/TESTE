package br.com.zapagendado.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Paleta: tinta noturna com um único acento de sinal.
val Tinta = Color(0xFF10161B)
val Superficie = Color(0xFF182229)
val SuperficieAlta = Color(0xFF1F2C34)
val Texto = Color(0xFFE7EDF2)
val TextoFraco = Color(0xFF8FA3B0)
val Sinal = Color(0xFF3BC9A8)
val Ambar = Color(0xFFF2A65A)
val Apagado = Color(0xFF5A6B77)

private val esquema = darkColorScheme(
    primary = Sinal,
    onPrimary = Tinta,
    secondary = Ambar,
    background = Tinta,
    onBackground = Texto,
    surface = Superficie,
    onSurface = Texto,
    surfaceVariant = SuperficieAlta,
    onSurfaceVariant = TextoFraco,
    outline = Color(0xFF2C3B45)
)

private val tipos = Typography(
    displaySmall = TextStyle(fontSize = 34.sp, fontWeight = FontWeight.Light, letterSpacing = (-1).sp),
    titleLarge = TextStyle(fontSize = 20.sp, fontWeight = FontWeight.SemiBold, letterSpacing = (-0.2).sp),
    titleMedium = TextStyle(fontSize = 16.sp, fontWeight = FontWeight.Medium),
    bodyLarge = TextStyle(fontSize = 15.sp, lineHeight = 21.sp),
    bodyMedium = TextStyle(fontSize = 13.sp, lineHeight = 18.sp),
    labelSmall = TextStyle(fontSize = 11.sp, fontWeight = FontWeight.Medium, letterSpacing = 1.2.sp)
)

@Composable
fun TemaZap(conteudo: @Composable () -> Unit) {
    MaterialTheme(colorScheme = esquema, typography = tipos, content = conteudo)
}
