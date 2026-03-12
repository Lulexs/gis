<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
  xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

  <NamedLayer>
    <Name>wards_layer</Name>

    <UserStyle>
      <Title>Tokyo Ward Borders</Title>

      <FeatureTypeStyle>

        <Rule>
          <Name>Ward Borders</Name>

          <PolygonSymbolizer>

            <Fill>
              <CssParameter name="fill">#ffffff</CssParameter>
              <CssParameter name="fill-opacity">0.05</CssParameter>
            </Fill>

            <Stroke>
              <CssParameter name="stroke">#333333</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
            </Stroke>

          </PolygonSymbolizer>

        </Rule>

        <Rule>
          <Name>Ward Labels</Name>

          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>name</ogc:PropertyName>
            </Label>

            <Font>
              <CssParameter name="font-family">Arial</CssParameter>
              <CssParameter name="font-size">11</CssParameter>
              <CssParameter name="font-style">normal</CssParameter>
              <CssParameter name="font-weight">bold</CssParameter>
            </Font>

            <Fill>
              <CssParameter name="fill">#222222</CssParameter>
            </Fill>

            <Halo>
              <Radius>1.5</Radius>
              <Fill>
                <CssParameter name="fill">#ffffff</CssParameter>
              </Fill>
            </Halo>

          </TextSymbolizer>

        </Rule>

      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>

</StyledLayerDescriptor>