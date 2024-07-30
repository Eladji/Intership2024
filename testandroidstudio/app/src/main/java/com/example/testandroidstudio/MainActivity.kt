package com.example.testandroidstudio

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }
        val connect = findViewById<Button>(R.id.connect)
        val email = findViewById<EditText>(R.id.mailconnect)
        val password = findViewById<EditText>(R.id.passwordconnect)
        val error = findViewById<TextView>(R.id.error)

        connect.setOnClickListener(View.OnClickListener { view : View ->
            error.visibility = View.GONE
            println("Hi")
            val txtemail = email.text.toString()
            val txtpassword = password.text.toString()
            if (txtemail.trim().isEmpty() || txtpassword.trim().isEmpty()){
                error.text = "Vous devez remplire tout les champs"
                error.visibility = View.VISIBLE
            }else{
                if(txtemail.trim() == "a" && txtpassword.trim() == "a"){
                    Intent(this, HomeActivity::class.java).also {
                        it.putExtra("email", txtemail)
                        startActivity(it)
                    }
                }
                else{
                    error.text = "Adresse email ou mot de passe incorrect"
                    error.visibility = View.VISIBLE
                }
            }
        })
    }
}