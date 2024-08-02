package com.example.testandroidstudio

import android.os.Bundle
import android.util.Log
import android.widget.TextView
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.LinearLayoutManager
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.RecyclerView
import com.example.myapplication.network.RetrofitInstance
import com.example.myapplication.network.User
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class HomeActivity : AppCompatActivity() {
    private lateinit var recyclerView: RecyclerView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_home)
        val txtemail = findViewById<TextView>(R.id.email)
        val email = intent.getStringExtra("email")
        //txtemail.text = "Bienvenu : $email"
        recyclerView = findViewById(R.id.recyclerView)
        recyclerView.layoutManager = LinearLayoutManager(this)

        // Fetch users
        fetchUsers()

    }

    private fun fetchUsers() {
        lifecycleScope.launch {
            try {
                val response = withContext(Dispatchers.IO) {
                    RetrofitInstance.api.getUsers()
                }
                // Handle the response (e.g., log it or update the UI)
                recyclerView.adapter = UserAdapter(response)
            } catch (e: Exception) {
                Toast.makeText(this@HomeActivity, "Failed to fetch data", Toast.LENGTH_SHORT).show()
                Log.e("HomeActivity", "Error: ${e.message}")
            }
        }
    }
}