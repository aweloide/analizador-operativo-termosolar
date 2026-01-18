Attribute VB_Name = "Cálculos"
' Caudal Masico
' Calcula el caudal másico (kg/s) a partir del caudal volumétrico (m³/h) y la densidad (kg/m³) del fluido.
' Uso en Excel: =QMass(Qvol, Densidad)
' Donde Qv es el caudal volumétrico en m³/h
'       Densidad es la densidad del fluido en kg/m³
Function QMass(Qvol As Double, Densidad As Double) As Double
    QMass = (Qvol / 3600) * Densidad
End Function

' Densidad
' Calcula la densidad (kg/m³) del fluido líquido en función de la temperatura T (°C).
' Donde T es la temperatura en grados Celsius (°C)
Function HTFDensity(T As Double) As Double
    HTFDensity = -0.90797 * T + 0.00078116 * T ^ 2 - 0.000002367 * T ^ 3 + 1083.25
End Function

' HeatCapacity
' Calcula la capacidad calorífica a presión constante (kJ/kg·K) del fluido líquido
' en función de la temperatura T (°C).
' Donde T es la temperatura en grados Celsius (°C)
Function HTFHeatCapacity(T As Double) As Double
    HTFHeatCapacity = 0.002414 * T + 0.0000059591 * T ^ 2 - 0.000000029879 * T ^ 3 + 0.000000000044172 * T ^ 4 + 1.498
End Function

' ThermalConductivity
' Calcula la conductividad térmica (W/m·K) del fluido líquido en función de la temperatura T (°C).
' Donde T es la temperatura en grados Celsius (°C)
Function HTFThermalCond(T As Double) As Double
    HTFThermalCond = -0.0000819477 * T - 0.000000192257 * T ^ 2 + 0.000000000025034 * T ^ 3 - 7.2974E-15 * T ^ 4 + 0.137743
End Function

' VapourPressure
' Calcula la presión de vapor (kPa) del fluido líquido en función de la temperatura T (°C).
' Donde T es la temperatura en grados Celsius (°C)
Function HTFVapourPress(T As Double) As Double
    HTFVapourPress = -0.190859 * T + 0.00435824 * T ^ 2 - 0.000036106 * T ^ 3 + 0.000000108408 * T ^ 4 + 2.12329
End Function

' Enthalpy
' Calcula la entalpía (kJ/kg) del fluido líquido en función de la temperatura T (°C).
' Donde T es la temperatura en grados Celsius (°C)
Function HTFEntalphy(T As Double) As Double
    HTFEntalphy = 1.51129 * T + 0.0012941 * T ^ 2 + 0.000000123697 * T ^ 3 - 0.62677
End Function

' LatentHeatVaporisation
' Calcula el calor latente de vaporización (kJ/kg) del fluido líquido en función de la temperatura T (°C).
' Donde T es la temperatura en grados Celsius (°C)
Function HTFLatentHeatVapor(T As Double) As Double
    HTFLatentHeatVapor = -0.528933 * T - 0.0000750103 * T ^ 2 + 0.0000015622 * T ^ 3 - 0.000000003771 * T ^ 4 + 425.18
End Function

