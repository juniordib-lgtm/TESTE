package br.com.zapagendado.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverter
import androidx.room.TypeConverters

class Conversores {
    @TypeConverter fun statusParaTexto(v: Status): String = v.name
    @TypeConverter fun textoParaStatus(v: String): Status = Status.valueOf(v)
    @TypeConverter fun repParaTexto(v: Repeticao): String = v.name
    @TypeConverter fun textoParaRep(v: String): Repeticao = Repeticao.valueOf(v)
}

@Database(entities = [Agendamento::class], version = 1, exportSchema = false)
@TypeConverters(Conversores::class)
abstract class AppDatabase : RoomDatabase() {

    abstract fun dao(): AgendamentoDao

    companion object {
        @Volatile private var instancia: AppDatabase? = null

        fun get(ctx: Context): AppDatabase = instancia ?: synchronized(this) {
            instancia ?: Room.databaseBuilder(
                ctx.applicationContext,
                AppDatabase::class.java,
                "zapagendado.db"
            ).build().also { instancia = it }
        }
    }
}
