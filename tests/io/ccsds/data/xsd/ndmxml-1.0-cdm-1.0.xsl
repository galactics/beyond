<?xml version="1.0" encoding="utf-8"?>

<!--********************************************************************--> 
<!-- NOTE: This is version 1.0 of the CDM/XML XSLT (06/17/2013).        --> 
<!--                                                                    --> 
<!-- Compatible document versions are:                                  --> 
<!-- CDM 508.0-B-1 Blue Book (06/2013)                                  -->
<!--                                                                    --> 
<!-- This style sheet will produce a CDM in the KVN format from an      -->
<!-- input CDM in the XML format.                                       -->
<!--                                                                    --> 
<!--********************************************************************--> 

<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:msxsl="urn:schemas-microsoft-com:xslt" 
exclude-result-prefixes="msxsl">

<xsl:output method="text" indent="yes"/> 

<xsl:strip-space elements="*"/>
<xsl:preserve-space elements="cdm segment"/> 

<xsl:template match="cdm[@id]">
<xsl:value-of select="@id"/> = <xsl:value-of select="@version"/>
<xsl:apply-templates/>
</xsl:template>
<xsl:template match="header/COMMENT">COMMENT <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="header/CREATION_DATE">
CREATION_DATE = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="header/ORIGINATOR">
ORIGINATOR = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="header/MESSAGE_FOR">
MESSAGE_FOR = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="header/MESSAGE_ID">
MESSAGE_ID = <xsl:value-of select="."/> 
</xsl:template> 

<xsl:template match="relativeMetadataData/COMMENT">
COMMENT <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="relativeMetadataData/TCA">
TCA = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="relativeMetadataData/MISS_DISTANCE[@units]">
MISS_DISTANCE = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="relativeMetadataData/RELATIVE_SPEED">RELATIVE_SPEED = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template> 

<xsl:template match="relativeMetadataData/relativeStateVector/RELATIVE_POSITION_R">RELATIVE_POSITION_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="relativeMetadataData/relativeStateVector/RELATIVE_POSITION_T">RELATIVE_POSITION_T = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="relativeMetadataData/relativeStateVector/RELATIVE_POSITION_N">RELATIVE_POSITION_N = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>] 
</xsl:template>

<xsl:template match="relativeMetadataData/relativeStateVector/RELATIVE_VELOCITY_R">RELATIVE_VELOCITY_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="relativeMetadataData/relativeStateVector/RELATIVE_VELOCITY_T">RELATIVE_VELOCITY_T = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="relativeMetadataData/relativeStateVector/RELATIVE_VELOCITY_N">RELATIVE_VELOCITY_N = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="relativeMetadataData/START_SCREEN_PERIOD">START_SCREEN_PERIOD = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="relativeMetadataData/STOP_SCREEN_PERIOD">
STOP_SCREEN_PERIOD = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="relativeMetadataData/SCREEN_VOLUME_FRAME">
SCREEN_VOLUME_FRAME = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="relativeMetadataData/SCREEN_VOLUME_SHAPE">
SCREEN_VOLUME_SHAPE = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="relativeMetadataData/SCREEN_VOLUME_X">
SCREEN_VOLUME_X = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="relativeMetadataData/SCREEN_VOLUME_Y">SCREEN_VOLUME_Y = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="relativeMetadataData/SCREEN_VOLUME_Z">SCREEN_VOLUME_Z = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template> 

<xsl:template  match="relativeMetadataData/SCREEN_ENTRY_TIME">SCREEN_ENTRY_TIME = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="relativeMetadataData/SCREEN_EXIT_TIME">
SCREEN_EXIT_TIME = <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="relativeMetadataData/COLLISION_PROBABILITY">
COLLISION_PROBABILITY = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="relativeMetadataData/COLLISION_PROBABILITY_METHOD">
COLLISION_PROBABILITY_METHOD = <xsl:value-of select="."/> 
</xsl:template> 

<xsl:template match="segment/metadata/COMMENT">
COMMENT <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="segment/metadata/OBJECT">
OBJECT = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/OBJECT_DESIGNATOR">
OBJECT_DESIGNATOR = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/CATALOG_NAME">
CATALOG_NAME = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/OBJECT_NAME">
OBJECT_NAME = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/INTERNATIONAL_DESIGNATOR">
INTERNATIONAL_DESIGNATOR = <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="segment/metadata/OBJECT_TYPE">
OBJECT_TYPE = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/OPERATOR_CONTACT_POSITION">
OPERATOR_CONTACT_POSITION = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/OPERATOR_ORGANIZATION">
OPERATOR_ORGANIZATION = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/OPERATOR_PHONE">
OPERATOR_PHONE = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/OPERATOR_EMAIL">
OPERATOR_EMAIL = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/EPHEMERIS_NAME">
EPHEMERIS_NAME = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/COVARIANCE_METHOD">
COVARIANCE_METHOD = <xsl:value-of select="."/> 
</xsl:template> 

<xsl:template match="segment/metadata/MANEUVERABLE">
MANEUVERABLE = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/ORBIT_CENTER">
ORBIT_CENTER = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/REF_FRAME">
REF_FRAME = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/GRAVITY_MODEL">
GRAVITY_MODEL = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/ATMOSPHERIC_MODEL">
ATMOSPHERIC_MODEL = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/N_BODY_PERTURBATIONS">
N_BODY_PERTURBATIONS = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/SOLAR_RAD_PRESSURE">
SOLAR_RAD_PRESSURE = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/EARTH_TIDES">
EARTH_TIDES = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/metadata/INTRACK_THRUST">
INTRACK_THRUST = <xsl:value-of select="."/> 
</xsl:template> 

<xsl:template match="segment/data/COMMENT">

COMMENT <xsl:value-of select="."/>
</xsl:template> 

<xsl:template match="segment/data/odParameters/COMMENT">
COMMENT <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="segment/data/odParameters/TIME_LASTOB_START">
TIME_LASTOB_START = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/data/odParameters/TIME_LASTOB_END">
TIME_LASTOB_END = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/data/odParameters/RECOMMENDED_OD_SPAN">
RECOMMENDED_OD_SPAN = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/odParameters/ACTUAL_OD_SPAN">ACTUAL_OD_SPAN = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/odParameters/OBS_AVAILABLE">OBS_AVAILABLE = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/data/odParameters/OBS_USED">
OBS_USED = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/data/odParameters/TRACKS_AVAILABLE">
TRACKS_AVAILABLE = <xsl:value-of select="."/> 
</xsl:template> 

<xsl:template match="segment/data/odParameters/TRACKS_USED">
TRACKS_USED = <xsl:value-of select="."/> 
</xsl:template>

<xsl:template match="segment/data/odParameters/RESIDUALS_ACCEPTED">
RESIDUALS_ACCEPTED = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/odParameters/WEIGHTED_RMS">WEIGHTED_RMS = <xsl:value-of select="."/> 
</xsl:template> 

<xsl:template match="segment/data/additionalParameters/COMMENT">
COMMENT <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="segment/data/additionalParameters/AREA_PC">
AREA_PC = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/additionalParameters/AREA_DRG">AREA_DRG = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/additionalParameters/AREA_SRP">AREA_SRP = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/additionalParameters/MASS">MASS = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/additionalParameters/CD_AREA_OVER_MASS">CD_AREA_OVER_MASS = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/additionalParameters/CR_AREA_OVER_MASS">CR_AREA_OVER_MASS = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/additionalParameters/THRUST_ACCELERATION">THRUST_ACCELERATION = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/additionalParameters/SEDR">SEDR = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template> 

<xsl:template match="segment/data/stateVector/COMMENT">
COMMENT <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="segment/data/stateVector/X">
X = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/stateVector/Y">Y = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/stateVector/Z">Z = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/stateVector/X_DOT">X_DOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/stateVector/Y_DOT">Y_DOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/stateVector/Z_DOT">Z_DOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template> 

<xsl:template match="segment/data/covarianceMatrix/COMMENT">
COMMENT <xsl:value-of select="."/>
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CR_R">
CR_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CT_R">CT_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CT_T">CT_T = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CN_R">CN_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CN_T">CN_T = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CN_N">CN_N = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CRDOT_R">CRDOT_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CRDOT_T">CRDOT_T = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CRDOT_N">CRDOT_N = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CRDOT_RDOT">CRDOT_RDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTDOT_R">CTDOT_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTDOT_T">CTDOT_T = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTDOT_N">CTDOT_N = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTDOT_RDOT">CTDOT_RDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTDOT_TDOT">CTDOT_TDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CNDOT_R">CNDOT_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CNDOT_T">CNDOT_T = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CNDOT_N">CNDOT_N = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CNDOT_RDOT">CNDOT_RDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CNDOT_TDOT">CNDOT_TDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CNDOT_NDOT">CNDOT_NDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CDRG_R">CDRG_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CDRG_T">CDRG_T = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CDRG_N">CDRG_N = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CDRG_RDOT">CDRG_RDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CDRG_TDOT">CDRG_TDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template> 

<xsl:template match="segment/data/covarianceMatrix/CDRG_NDOT">CDRG_NDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CDRG_DRG">CDRG_DRG = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CSRP_R">CSRP_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CSRP_T">CSRP_T = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CSRP_N">CSRP_N = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CSRP_RDOT">CSRP_RDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CSRP_TDOT">CSRP_TDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CSRP_NDOT">CSRP_NDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CSRP_DRG">CSRP_DRG = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CSRP_SRP">CSRP_SRP = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTHR_R">CTHR_R = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTHR_T">CTHR_T = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTHR_N">CTHR_N = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTHR_RDOT">CTHR_RDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTHR_TDOT">CTHR_TDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTHR_NDOT">CTHR_NDOT = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTHR_DRG">CTHR_DRG = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTHR_SRP">CTHR_SRP = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template>

<xsl:template match="segment/data/covarianceMatrix/CTHR_THR">CTHR_THR = <xsl:value-of select="."/> [<xsl:value-of select="@units"/>]
</xsl:template> 

</xsl:stylesheet> 
