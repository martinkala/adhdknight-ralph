package com.example.madhdtracker.domain.model

data class Category(
    val key: String,
    val label: String,
    val clickable: Boolean,
    val weight: Double
)

data class Element(
    val key: String,
    val weight: Double,
    val impact: Int,
    val parent: String?,
    val description: String,
    val active: Boolean,
    val scale: List<Int>?
)

data class ElementConfig(
    val categories: Map<String, Category>,
    val elements: Map<String, Element>
) {
    val negativeKeys: Set<String>
        get() = elements.filter { it.value.impact == -1 }.keys.toSet()

    val positiveKeys: Set<String>
        get() = elements.filter { it.value.impact == 1 }.keys.toSet()
}
