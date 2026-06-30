package com.example.madhdtracker.domain.model

data class EntityNode(
    val key: String,
    val weight: Double,
    val impact: Int?,
    val parent: String?,
    val label: String,
    val active: Boolean,
    val scale: List<Int>?,
    val clickable: Boolean
)

data class EntityConfig(
    val nodes: Map<String, EntityNode>
) {
    val negativeKeys: Set<String>
        get() = nodes.values.filter { it.impact == -1 && it.active }.map { it.key }.toSet()

    val positiveKeys: Set<String>
        get() = nodes.values.filter { it.impact == 1 && it.active }.map { it.key }.toSet()

    val trackableNodes: Map<String, EntityNode>
        get() = nodes.filter { it.value.impact != null && it.value.active }

    val groupNodes: Map<String, EntityNode>
        get() = nodes.filter { it.value.impact == null }

    val trackableKeys: Set<String>
        get() = trackableNodes.keys
}
