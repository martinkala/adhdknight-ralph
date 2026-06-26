package com.example.madhdtracker.data

object DefaultWeights {
    val weights: Map<String, Double> = mapOf(
        "overall_feeling" to 13.0,
        "sleep" to 15.0,
        "physical_activity" to 11.0,
        "stress_work" to 13.0,
        "stress_personal" to 13.0,
        "nutrition_protein" to 8.0,
        "caffeine" to 6.0,
        "alcohol" to 10.0,
        "mindfulness" to 11.0
    )

    // Pre tieto elementy platí: vyššia hodnota = horšie → invertujeme pri výpočte
    val negativeKeys: Set<String> = setOf("stress_work", "stress_personal", "alcohol", "caffeine")
}
