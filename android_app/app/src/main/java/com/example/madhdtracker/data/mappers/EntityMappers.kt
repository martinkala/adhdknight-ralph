package com.example.madhdtracker.data.mappers

import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.WeightEntity
import com.example.madhdtracker.domain.model.ElementValue
import com.example.madhdtracker.domain.model.WeightProfile

fun EventValueEntity.toDomain(): ElementValue {
    return ElementValue(
        elementKey = elementKey,
        valueBinary = valueBinary,
        valueScale = valueScale,
        valueEffective = valueEffective
    )
}

fun WeightEntity.toDomain(): WeightProfile {
    return WeightProfile(
        elementKey = elementKey,
        weightDefault = weightDefault,
        weightPersonal = weightPersonal
    )
}
